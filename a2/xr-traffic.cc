/*
 * A2 — 3GPP XR downlink video traffic generator for ns-3.
 *
 * Model: 3GPP TR 38.838 single-stream DL video model, as referenced by
 * 3GPP TR 26.926 V19.0.0 clauses 6.5.3.1 (frame size) and 6.5.3.2 (jitter):
 *   - periodic frame arrivals, period T = 1/fps
 *   - jitter added ON TOP of the periodic schedule:  t_k = t0 + k*T + J_k,
 *       J_k ~ truncated Gaussian(mean 0, STD 2 ms), |J_k| <= 4 ms
 *   - frame size ~ truncated Gaussian(mean M = R/(fps*8) bytes, STD 10.5% of M),
 *       Min 50% of M, Max 150% of M   (one frame carries both eyes)
 *   - each frame is split into UDP packets of at most maxPayload bytes (IP packet <= 1500 B MTU),
 *     all handed to the socket at the frame's arrival instant
 *
 * Outputs:
 *   xr-frames.csv    frame_id,t_nominal_s,t_send_s,jitter_ms,frame_bytes,n_packets,iat_s
 *   xr-packets.csv   t_send_s,frame_id,size_bytes
 *   a2-xr-0-0.pcap   sender-side capture (open in Wireshark)
 *   stdout           send failures + FlowMonitor throughput / delay / loss / packets over PDB
 *
 * Put this file in ns-3-dev/scratch/ and run:  ./ns3 run xr-traffic
 */
#include "ns3/applications-module.h"
#include "ns3/core-module.h"
#include "ns3/flow-monitor-module.h"
#include "ns3/internet-module.h"
#include "ns3/network-module.h"
#include "ns3/point-to-point-module.h"

#include <algorithm>
#include <fstream>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("A2XrTraffic");

namespace
{
Ptr<Socket> g_src;
Ptr<NormalRandomVariable> g_frameBytes; // truncated Gaussian, bytes
Ptr<NormalRandomVariable> g_jitterMs;   // truncated Gaussian, ms, mean 0
double g_t0 = 1.0;                      // start of the periodic schedule (s)
double g_period = 1.0 / 60.0;           // T = 1/fps (s)
uint32_t g_maxPayload = 1400;
uint32_t g_nFrames = 600;
double g_prevSend = 0.0;
uint64_t g_sendFailures = 0;
uint64_t g_bytesOffered = 0;
std::ofstream g_frames;
std::ofstream g_packets;
} // namespace

void
GenerateFrame(uint32_t k, double jitterMs)
{
    double now = Simulator::Now().GetSeconds();
    double bytes = g_frameBytes->GetValue();
    auto frameBytes = static_cast<uint32_t>(std::max(1.0, bytes + 0.5));

    uint32_t nPackets = 0;
    for (uint32_t left = frameBytes; left > 0;)
    {
        uint32_t sz = std::min(left, g_maxPayload);
        if (g_src->Send(Create<Packet>(sz)) < 0)
        {
            g_sendFailures++;
        }
        g_packets << now << "," << k << "," << sz << "\n";
        g_bytesOffered += sz;
        left -= sz;
        nPackets++;
    }

    double iat = (k == 0) ? 0.0 : (now - g_prevSend);
    g_frames << k << "," << g_t0 + k * g_period << "," << now << "," << jitterMs << ","
             << frameBytes << "," << nPackets << "," << iat << "\n";
    g_prevSend = now;

    // next frame: periodic slot k+1 plus its own jitter (not accumulated)
    if (k + 1 < g_nFrames)
    {
        double j = g_jitterMs->GetValue();
        double tNext = g_t0 + (k + 1) * g_period + j / 1000.0;
        Simulator::Schedule(Seconds(std::max(0.0, tNext - now)), &GenerateFrame, k + 1, j);
    }
}

int
main(int argc, char* argv[])
{
    double dataRateMbps = 30.0; // R: 30 Mbit/s (VR/AR default), 45 optional
    double fps = 60.0;          // F
    double sizeStdPct = 10.5;   // STD, % of mean
    double sizeMinPct = 50.0;   // Min, % of mean
    double sizeMaxPct = 150.0;  // Max, % of mean
    double jitterStdMs = 2.0;   // jitter STD
    double jitterBndMs = 4.0;   // jitter range [-bnd, +bnd] (5 is the optional value)
    double pdbMs = 10.0;        // packet delay budget: 10 ms VR, 15 ms cloud gaming
    uint32_t maxPayload = 1400;
    uint32_t nFrames = 600; // 10 s at 60 fps
    uint32_t seed = 1;

    CommandLine cmd(__FILE__);
    cmd.AddValue("dataRateMbps", "Average data rate R (Mbit/s)", dataRateMbps);
    cmd.AddValue("fps", "Frame rate F (fps)", fps);
    cmd.AddValue("sizeStdPct", "Frame-size STD as % of mean", sizeStdPct);
    cmd.AddValue("sizeMinPct", "Frame-size minimum as % of mean", sizeMinPct);
    cmd.AddValue("sizeMaxPct", "Frame-size maximum as % of mean", sizeMaxPct);
    cmd.AddValue("jitterStdMs", "Jitter STD (ms)", jitterStdMs);
    cmd.AddValue("jitterBndMs", "Jitter truncation, +/- (ms)", jitterBndMs);
    cmd.AddValue("pdbMs", "Packet delay budget to check against (ms)", pdbMs);
    cmd.AddValue("maxPayload", "Max UDP payload per packet (bytes)", maxPayload);
    cmd.AddValue("nFrames", "Number of frames", nFrames);
    cmd.AddValue("seed", "RNG run number", seed);
    cmd.Parse(argc, argv);

    // ns-3's NormalRandomVariable truncates symmetrically around the mean
    NS_ABORT_MSG_IF(std::abs((100.0 - sizeMinPct) - (sizeMaxPct - 100.0)) > 1e-9,
                    "sizeMinPct/sizeMaxPct must be symmetric around 100%");
    NS_ABORT_MSG_IF(jitterBndMs >= 500.0 / fps, "jitter bound must be < T/2 to keep frame order");

    RngSeedManager::SetRun(seed);
    g_period = 1.0 / fps;
    g_nFrames = nFrames;
    g_maxPayload = maxPayload;

    double meanBytes = dataRateMbps * 1e6 / (fps * 8.0);
    double stdBytes = meanBytes * sizeStdPct / 100.0;
    g_frameBytes = CreateObject<NormalRandomVariable>();
    g_frameBytes->SetAttribute("Mean", DoubleValue(meanBytes));
    g_frameBytes->SetAttribute("Variance", DoubleValue(stdBytes * stdBytes));
    g_frameBytes->SetAttribute("Bound", DoubleValue(meanBytes * (sizeMaxPct - 100.0) / 100.0));

    g_jitterMs = CreateObject<NormalRandomVariable>();
    g_jitterMs->SetAttribute("Mean", DoubleValue(0.0));
    g_jitterMs->SetAttribute("Variance", DoubleValue(jitterStdMs * jitterStdMs));
    g_jitterMs->SetAttribute("Bound", DoubleValue(jitterBndMs));

    // n0 (sender) ---- 200 Mbps / 5 ms ---- n1 (receiver)
    NodeContainer nodes;
    nodes.Create(2);

    PointToPointHelper p2p;
    p2p.SetDeviceAttribute("DataRate", StringValue("200Mbps"));
    p2p.SetChannelAttribute("Delay", StringValue("5ms"));
    NetDeviceContainer devices = p2p.Install(nodes);

    InternetStackHelper stack;
    stack.Install(nodes);
    Ipv4AddressHelper address;
    address.SetBase("10.1.1.0", "255.255.255.0");
    Ipv4InterfaceContainer ifaces = address.Assign(devices);

    uint16_t port = 40000; // no Wireshark dissector on this port, so it shows as plain UDP
    PacketSinkHelper sink("ns3::UdpSocketFactory", InetSocketAddress(Ipv4Address::GetAny(), port));
    ApplicationContainer sinkApp = sink.Install(nodes.Get(1));
    sinkApp.Start(Seconds(0.0));

    g_src = Socket::CreateSocket(nodes.Get(0), UdpSocketFactory::GetTypeId());
    g_src->Connect(InetSocketAddress(ifaces.GetAddress(1), port));

    g_frames.open("xr-frames.csv");
    g_frames << "frame_id,t_nominal_s,t_send_s,jitter_ms,frame_bytes,n_packets,iat_s\n";
    g_packets.open("xr-packets.csv");
    g_packets << "t_send_s,frame_id,size_bytes\n";
    double j0 = g_jitterMs->GetValue();
    Simulator::Schedule(Seconds(g_t0 + j0 / 1000.0), &GenerateFrame, 0u, j0);

    p2p.EnablePcapAll("a2-xr");
    FlowMonitorHelper fmHelper;
    Ptr<FlowMonitor> monitor = fmHelper.InstallAll();

    Simulator::Stop(Seconds(g_t0 + nFrames / fps + 2.0));
    Simulator::Run();

    double genS = nFrames / fps;
    std::cout << "Generated  : " << nFrames << " frames, " << g_bytesOffered << " bytes ("
              << g_bytesOffered * 8.0 / genS / 1e6 << " Mbps offered)\n"
              << "Send fails : " << g_sendFailures << "\n";

    monitor->CheckForLostPackets();
    auto classifier = DynamicCast<Ipv4FlowClassifier>(fmHelper.GetClassifier());
    for (const auto& [id, st] : monitor->GetFlowStats())
    {
        Ipv4FlowClassifier::FiveTuple t = classifier->FindFlow(id);
        double durS = (st.timeLastRxPacket - st.timeFirstTxPacket).GetSeconds();
        double thrMbps = durS > 0 ? st.rxBytes * 8.0 / durS / 1e6 : 0.0;
        double delayMs = st.rxPackets ? st.delaySum.GetSeconds() / st.rxPackets * 1e3 : 0.0;
        // packets whose one-way delay exceeds the PDB (FlowMonitor delay histogram, 1 ms bins)
        uint64_t overPdb = 0;
        for (uint32_t b = 0; b < st.delayHistogram.GetNBins(); ++b)
        {
            if (st.delayHistogram.GetBinStart(b) >= pdbMs / 1000.0 - 1e-12)
            {
                overPdb += st.delayHistogram.GetBinCount(b);
            }
        }
        std::cout << "Flow " << id << "  " << t.sourceAddress << " -> " << t.destinationAddress
                  << "\n  Tx packets : " << st.txPackets << "\n  Rx packets : " << st.rxPackets
                  << "\n  Lost       : " << st.lostPackets << "\n  Rx bytes   : " << st.rxBytes
                  << "\n  Throughput : " << thrMbps << " Mbps (IP layer, incl. headers)"
                  << "\n  Mean delay : " << delayMs << " ms"
                  << "\n  Over PDB   : " << overPdb << " packets with delay >= " << pdbMs
                  << " ms\n";
    }

    g_frames.close();
    g_packets.close();
    Simulator::Destroy();
    return 0;
}
