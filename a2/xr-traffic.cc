/*
 * A2 — 3GPP-style XR/cloud-gaming video traffic generator for ns-3.
 *
 * Model (frame-based, after 3GPP TS 26.926 / TR 38.838 XR methodology):
 *   - one video frame per period 1/fps
 *   - frame inter-arrival = 1/fps + jitter,  jitter ~ truncated N(0, jitterStd), |jitter| <= jitterBnd
 *   - frame size ~ truncated N(mean = rate/fps, std = sizeStdPct% of mean), cut at +/- 3 sigma
 *   - each frame is split into UDP packets of at most maxPayload bytes (IP packet <= 1500 B MTU),
 *     all handed to the socket at the frame's generation instant
 *
 * Outputs:
 *   xr-frames.csv    frame_id,t_send_s,frame_bytes,n_packets,iat_s   (frame level: compare to model)
 *   xr-packets.csv   t_send_s,frame_id,size_bytes                    (packet level)
 *   a2-xr-0-0.pcap   sender-side capture (open in Wireshark)
 *   stdout           send failures + FlowMonitor throughput / delay / loss
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
Ptr<NormalRandomVariable> g_frameBytes; // truncated normal, bytes
Ptr<NormalRandomVariable> g_jitterMs;   // truncated normal, ms, mean 0
double g_fps = 60.0;
uint32_t g_maxPayload = 1400;
uint32_t g_frameNo = 0;
uint32_t g_nFrames = 600;
double g_prevTime = 0.0;
uint64_t g_sendFailures = 0;
uint64_t g_bytesOffered = 0;
std::ofstream g_frames;
std::ofstream g_packets;
} // namespace

void
GenerateFrame()
{
    if (g_frameNo >= g_nFrames)
    {
        return;
    }

    double bytes = g_frameBytes->GetValue();
    auto frameBytes = static_cast<uint32_t>(std::max(1.0, bytes + 0.5));

    double now = Simulator::Now().GetSeconds();
    uint32_t nPackets = 0;
    for (uint32_t left = frameBytes; left > 0;)
    {
        uint32_t sz = std::min(left, g_maxPayload);
        if (g_src->Send(Create<Packet>(sz)) < 0)
        {
            g_sendFailures++;
        }
        g_packets << now << "," << g_frameNo << "," << sz << "\n";
        g_bytesOffered += sz;
        left -= sz;
        nPackets++;
    }

    double iat = (g_frameNo == 0) ? 0.0 : (now - g_prevTime);
    g_frames << g_frameNo << "," << now << "," << frameBytes << "," << nPackets << "," << iat
             << "\n";
    g_prevTime = now;
    g_frameNo++;

    double nextS = 1.0 / g_fps + g_jitterMs->GetValue() / 1000.0;
    Simulator::Schedule(Seconds(std::max(0.0, nextS)), &GenerateFrame);
}

int
main(int argc, char* argv[])
{
    double dataRateMbps = 30.0; // target media bitrate
    double fps = 60.0;
    double sizeStdPct = 10.5; // frame-size std, % of mean
    double jitterStdMs = 2.0; // frame arrival jitter std
    double jitterBndMs = 4.0; // jitter truncation (+/-)
    uint32_t maxPayload = 1400;
    uint32_t nFrames = 600; // 10 s at 60 fps
    uint32_t seed = 1;

    CommandLine cmd(__FILE__);
    cmd.AddValue("dataRateMbps", "Target media bitrate (Mbps)", dataRateMbps);
    cmd.AddValue("fps", "Frames per second", fps);
    cmd.AddValue("sizeStdPct", "Frame-size std as % of mean", sizeStdPct);
    cmd.AddValue("jitterStdMs", "Frame arrival jitter std (ms)", jitterStdMs);
    cmd.AddValue("jitterBndMs", "Frame arrival jitter truncation (ms)", jitterBndMs);
    cmd.AddValue("maxPayload", "Max UDP payload per packet (bytes)", maxPayload);
    cmd.AddValue("nFrames", "Number of frames", nFrames);
    cmd.AddValue("seed", "RNG run number", seed);
    cmd.Parse(argc, argv);

    RngSeedManager::SetRun(seed);
    g_fps = fps;
    g_nFrames = nFrames;
    g_maxPayload = maxPayload;

    double meanBytes = dataRateMbps * 1e6 / fps / 8.0;
    double stdBytes = meanBytes * sizeStdPct / 100.0;
    g_frameBytes = CreateObject<NormalRandomVariable>();
    g_frameBytes->SetAttribute("Mean", DoubleValue(meanBytes));
    g_frameBytes->SetAttribute("Variance", DoubleValue(stdBytes * stdBytes));
    g_frameBytes->SetAttribute("Bound", DoubleValue(3.0 * stdBytes));

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
    g_frames << "frame_id,t_send_s,frame_bytes,n_packets,iat_s\n";
    g_packets.open("xr-packets.csv");
    g_packets << "t_send_s,frame_id,size_bytes\n";
    Simulator::Schedule(Seconds(1.0), &GenerateFrame);

    p2p.EnablePcapAll("a2-xr");
    FlowMonitorHelper fmHelper;
    Ptr<FlowMonitor> monitor = fmHelper.InstallAll();

    Simulator::Stop(Seconds(1.0 + nFrames / fps + 2.0));
    Simulator::Run();

    double genS = nFrames / fps;
    std::cout << "Generated  : " << g_frameNo << " frames, " << g_bytesOffered << " bytes ("
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
        std::cout << "Flow " << id << "  " << t.sourceAddress << " -> " << t.destinationAddress
                  << "\n  Tx packets : " << st.txPackets << "\n  Rx packets : " << st.rxPackets
                  << "\n  Lost       : " << st.lostPackets << "\n  Rx bytes   : " << st.rxBytes
                  << "\n  Throughput : " << thrMbps << " Mbps (IP layer, incl. headers)"
                  << "\n  Mean delay : " << delayMs << " ms\n";
    }

    g_frames.close();
    g_packets.close();
    Simulator::Destroy();
    return 0;
}
