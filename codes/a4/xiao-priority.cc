/*
 * A4 — ns-3 reproduction of Y. Xiao, "Performance analysis of priority schemes for IEEE 802.11
 * and IEEE 802.11e wireless LANs," IEEE Trans. Wireless Commun. 4(4):1506-1515, 2005 —
 * Table I, Figs. 2-4 (combined scheme vs n) and Figs. 5, 7, 9 (one knob at a time).
 *
 * Scenario (paper Sections V-VI):
 *   - 1 AP + n0 class-0 and n1 class-1 stations, all within 5 m of the AP (ideal channel)
 *   - every station is always backlogged and carries one class, uplink to the AP
 *   - IEEE 802.11a, 6 Mb/s for data and control, basic access (no RTS/CTS)
 *   - per class: initial window W0, window-increasing factor sigma, retry limit L, CWmax 1024;
 *     equal DIFS for all classes
 *   The stations are non-QoS (DCF), so each one keeps its own CWmin/CWmax instead of adopting
 *   the AP's EDCA Parameter Set; sigma needs txop-cw-growth.patch (attribute
 *   ns3::Txop::CwGrowthFactor). ns-3 counts transmission attempts, Xiao counts retransmissions:
 *   FrameRetryLimit = L + 1, so that a frame is dropped after L + 1 failed attempts.
 *   Frame size: the paper's frame is 28 B MAC header + FCS + 1024 B payload = 1052 B. ns-3 adds
 *   an 8-byte LLC/SNAP header (24 + 4 + 8 = 36 B), so the payload sent is 1016 B, which keeps
 *   the PSDU at 1052 B; throughput is counted as delivered frames x 1024 B, as in the paper.
 *
 * Outputs (stdout, one CSV line):
 *   n0,n1,seed,W0_0,W0_1,sigma0,sigma1,L0,L1,S0,S1,D0_ms,D1_ms,P0,P1,acked0,acked1,drop0,drop1,
 *   associated
 *   S = normalized throughput (delivered frames x 1024 B x 8 / time / 6 Mb/s),
 *   D = mean delay of delivered frames from head-of-line to ACK (Xiao eq. 21),
 *   P = frame-dropping probability, dropped / (delivered + dropped) frames (Xiao eq. 16).
 *   Traffic starts once all stations are associated; statistics start 1 s later and last
 *   --statTime seconds.
 *
 * Run:  ./ns3 run "xiao-priority --n0=10 --n1=10 --seed=1"
 */
#include "ns3/core-module.h"
#include "ns3/mobility-module.h"
#include "ns3/network-module.h"
#include "ns3/wifi-module.h"

#include <map>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("A4XiaoPriority");

namespace
{
const uint32_t PAPER_PAYLOAD = 1024; // bytes counted per delivered frame
double g_statStart = 1e9;           // set once all stations are associated
double g_statEnd = 1e9;
uint32_t g_nSta = 0;
uint32_t g_assoc = 0;
std::vector<int> g_class;                      // class of each station
std::map<uint32_t, double> g_hol;              // station -> time its head-of-line frame started
uint64_t g_acked[2] = {0, 0};
uint64_t g_drops[2] = {0, 0};
double g_delaySum[2] = {0, 0};
double g_statTime = 20.0;
bool g_started = false;
NodeContainer g_stas;
NetDeviceContainer g_staDevs;
Address g_apAddr;
uint32_t g_payload = 1016;

bool
InWindow(double now)
{
    return now >= g_statStart && now < g_statEnd;
}

void
OnAcked(uint32_t sta, Ptr<const WifiMpdu> mpdu)
{
    if (!mpdu->GetHeader().IsData())
    {
        return;
    }
    double now = Simulator::Now().GetSeconds();
    auto it = g_hol.find(sta);
    if (it != g_hol.end() && InWindow(now))
    {
        int c = g_class[sta];
        g_acked[c]++;
        g_delaySum[c] += now - it->second;
    }
    g_hol[sta] = now; // saturated: the next frame is head-of-line from now
}

void
OnDropped(uint32_t sta, WifiMacDropReason reason, Ptr<const WifiMpdu> mpdu)
{
    if (reason != WIFI_MAC_DROP_REACHED_RETRY_LIMIT || !mpdu->GetHeader().IsData())
    {
        return;
    }
    double now = Simulator::Now().GetSeconds();
    if (g_hol.count(sta) && InWindow(now))
    {
        g_drops[g_class[sta]]++;
    }
    g_hol[sta] = now;
}

void
StartTraffic()
{
    if (g_started)
    {
        return;
    }
    g_started = true;
    double now = Simulator::Now().GetSeconds();
    // 6 Mb/s offered per station: always backlogged. Applications added while the simulation
    // runs are initialized at once, so the start time is relative to now.
    Time interval = Seconds(g_payload * 8.0 / 6e6);
    Ptr<UniformRandomVariable> jitter = CreateObject<UniformRandomVariable>();
    for (uint32_t i = 0; i < g_stas.GetN(); ++i)
    {
        PacketSocketAddress remote;
        remote.SetSingleDevice(g_staDevs.Get(i)->GetIfIndex());
        remote.SetPhysicalAddress(g_apAddr);
        remote.SetProtocol(1);
        Ptr<PacketSocketClient> client = CreateObject<PacketSocketClient>();
        client->SetRemote(remote);
        client->SetAttribute("PacketSize", UintegerValue(g_payload));
        client->SetAttribute("MaxPackets", UintegerValue(0));
        client->SetAttribute("Interval", TimeValue(interval));
        client->SetStartTime(Seconds(0.01 * jitter->GetValue()));
        g_stas.Get(i)->AddApplication(client);
    }
    g_statStart = now + 1.0;
    g_statEnd = g_statStart + g_statTime;
    Simulator::Stop(Seconds(g_statEnd - now));
}

void
OnAssoc(Mac48Address)
{
    if (++g_assoc == g_nSta)
    {
        StartTraffic();
    }
}

void
ConfigureDcf(Ptr<NetDevice> dev, uint32_t w0, uint32_t cwMax, double sigma, uint32_t retryLimit)
{
    Ptr<WifiMac> mac = DynamicCast<WifiNetDevice>(dev)->GetMac();
    mac->SetAttribute("FrameRetryLimit", UintegerValue(retryLimit + 1)); // attempts = L + 1
    PointerValue ptr;
    mac->GetAttribute("Txop", ptr);
    auto txop = ptr.Get<Txop>();
    txop->SetMinCws({w0 - 1}); // ns-3 stores CW = W - 1
    txop->SetMaxCws({cwMax - 1});
    txop->SetAifsns({2}); // DIFS = SIFS + 2 slots for every class
    txop->SetTxopLimits({Seconds(0)});
    txop->SetAttribute("CwGrowthFactor", DoubleValue(sigma));
}
} // namespace

int
main(int argc, char* argv[])
{
    uint32_t n[2] = {10, 10};
    uint32_t w0[2] = {16, 32};
    double sigma[2] = {1.7, 2.0};
    uint32_t L[2] = {4, 7};
    uint32_t cwMax = 1024;
    uint32_t seed = 1;
    double assocTimeout = 30.0;

    CommandLine cmd(__FILE__);
    cmd.AddValue("n0", "Number of class-0 stations", n[0]);
    cmd.AddValue("n1", "Number of class-1 stations", n[1]);
    cmd.AddValue("w00", "Initial window W of class 0", w0[0]);
    cmd.AddValue("w10", "Initial window W of class 1", w0[1]);
    cmd.AddValue("sigma0", "Window-increasing factor of class 0", sigma[0]);
    cmd.AddValue("sigma1", "Window-increasing factor of class 1", sigma[1]);
    cmd.AddValue("L0", "Retry limit (retransmissions) of class 0", L[0]);
    cmd.AddValue("L1", "Retry limit (retransmissions) of class 1", L[1]);
    cmd.AddValue("cwMax", "Maximum window W (both classes)", cwMax);
    cmd.AddValue("payload", "Payload sent per frame (bytes); 1016 + 36 = the paper's 1052 B PSDU",
                 g_payload);
    cmd.AddValue("statTime", "Measurement time after association + 1 s (s)", g_statTime);
    cmd.AddValue("seed", "RNG run number", seed);
    cmd.Parse(argc, argv);

    // Saturated queues hold frames older than WifiMacQueue's default 500 ms lifetime. A head-of-line
    // frame would then expire during its retries and be reported as EXPIRED_LIFETIME instead of
    // REACHED_RETRY_LIMIT, which hides retry-limit drops; the MAC behaviour is the same either way.
    Config::SetDefault("ns3::WifiMacQueue::MaxDelay", TimeValue(Seconds(3600)));

    RngSeedManager::SetSeed(1);
    RngSeedManager::SetRun(seed);

    g_nSta = n[0] + n[1];
    NodeContainer ap;
    ap.Create(1);
    NodeContainer& stas = g_stas;
    stas.Create(g_nSta);
    for (int c = 0; c < 2; ++c)
    {
        g_class.insert(g_class.end(), n[c], c);
    }

    YansWifiChannelHelper channel = YansWifiChannelHelper::Default();
    YansWifiPhyHelper phy;
    phy.SetChannel(channel.Create());

    WifiHelper wifi;
    wifi.SetStandard(WIFI_STANDARD_80211a);
    wifi.SetRemoteStationManager("ns3::ConstantRateWifiManager",
                                 "DataMode", StringValue("OfdmRate6Mbps"),
                                 "ControlMode", StringValue("OfdmRate6Mbps"),
                                 "RtsCtsThreshold", UintegerValue(4692)); // basic access

    WifiMacHelper mac;
    Ssid ssid("xiao");
    // with a very small retry limit (Fig. 9, L1 = 0, 1) the channel is so busy that 10 beacons in a
    // row can be lost; the default MaxMissedBeacons would then make a station re-associate, which
    // the paper's model does not have
    mac.SetType("ns3::StaWifiMac", "Ssid", SsidValue(ssid), "QosSupported", BooleanValue(false),
                "MaxMissedBeacons", UintegerValue(1000000));
    g_staDevs = wifi.Install(phy, mac, stas);
    NetDeviceContainer& staDevs = g_staDevs;
    mac.SetType("ns3::ApWifiMac", "Ssid", SsidValue(ssid), "QosSupported", BooleanValue(false));
    NetDeviceContainer apDev = wifi.Install(phy, mac, ap);
    for (uint32_t i = 0; i < g_nSta; ++i)
    {
        int c = g_class[i];
        ConfigureDcf(staDevs.Get(i), w0[c], cwMax, sigma[c], L[c]);
    }

    MobilityHelper mobility;
    Ptr<ListPositionAllocator> pos = CreateObject<ListPositionAllocator>();
    pos->Add(Vector(0, 0, 0));
    for (uint32_t i = 0; i < g_nSta; ++i)
    {
        double a = 2 * M_PI * i / g_nSta;
        pos->Add(Vector(5 * std::cos(a), 5 * std::sin(a), 0));
    }
    mobility.SetPositionAllocator(pos);
    mobility.SetMobilityModel("ns3::ConstantPositionMobilityModel");
    mobility.Install(ap);
    mobility.Install(stas);

    PacketSocketHelper packetSocket;
    packetSocket.Install(ap);
    packetSocket.Install(stas);

    PacketSocketAddress local;
    local.SetSingleDevice(apDev.Get(0)->GetIfIndex());
    local.SetProtocol(1);
    Ptr<PacketSocketServer> server = CreateObject<PacketSocketServer>();
    server->SetLocal(local);
    ap.Get(0)->AddApplication(server);
    g_apAddr = apDev.Get(0)->GetAddress();

    // the saturating clients are created in StartTraffic(), once all stations are associated
    for (uint32_t i = 0; i < g_nSta; ++i)
    {
        auto wmac = DynamicCast<WifiNetDevice>(staDevs.Get(i))->GetMac();
        wmac->TraceConnectWithoutContext("AckedMpdu", MakeBoundCallback(&OnAcked, i));
        wmac->TraceConnectWithoutContext("DroppedMpdu", MakeBoundCallback(&OnDropped, i));
        wmac->TraceConnectWithoutContext("Assoc", MakeCallback(&OnAssoc));
    }

    // if not every station has associated by then, start anyway; "associated" reports it
    Simulator::Schedule(Seconds(assocTimeout), &StartTraffic);
    Simulator::Run();

    double S[2];
    double D[2];
    double P[2];
    for (int c = 0; c < 2; ++c)
    {
        S[c] = g_acked[c] * PAPER_PAYLOAD * 8.0 / g_statTime / 6e6;
        D[c] = g_acked[c] ? g_delaySum[c] / g_acked[c] * 1e3 : 0.0;
        double tot = g_acked[c] + g_drops[c];
        P[c] = tot ? g_drops[c] / tot : 0.0;
    }
    std::cout << "n0,n1,seed,W0_0,W0_1,sigma0,sigma1,L0,L1,S0,S1,D0_ms,D1_ms,P0,P1,acked0,acked1,"
                 "drop0,drop1,associated\n"
              << n[0] << "," << n[1] << "," << seed << "," << w0[0] << "," << w0[1] << ","
              << sigma[0] << "," << sigma[1] << "," << L[0] << "," << L[1] << "," << S[0] << ","
              << S[1] << "," << D[0] << "," << D[1] << "," << P[0] << "," << P[1] << ","
              << g_acked[0] << "," << g_acked[1] << "," << g_drops[0] << "," << g_drops[1] << ","
              << g_assoc << std::endl;

    Simulator::Destroy();
    return 0;
}
