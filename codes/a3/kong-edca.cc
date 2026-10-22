/*
 * A3 — ns-3 reproduction setup for Kong, Tsang, Bensaou & Gao,
 * "Performance analysis of IEEE 802.11e contention-based channel access,"
 * IEEE JSAC 22(10):2095-2106, 2004 — Table I, Figs. 7-8.
 *
 * Scenario (paper Section V):
 *   - infrastructure BSS: 1 AP + M stations, ideal channel (all within 5 m of the AP)
 *   - every station has two saturated uplink ACs: AC3 (high priority) and AC1 (low)
 *   - IEEE 802.11b DSSS, 11 Mb/s data and control rate, long PHY header (192 us)
 *   - RTS/CTS for every data frame, one frame per TXOP (TXOP limit 0)
 *   - Table I: slot 20 us, SIFS = 1 slot, AIFS[AC3] = 3 slots, AIFS[AC1] = 4 slots,
 *              CW[AC3] = {15..127}, CW[AC1] = {31..255}, payload 1000 bytes
 *   AC3 -> ns-3 AC_VO (user priority 6), AC1 -> ns-3 AC_BK (user priority 1).
 *   AIFS = SIFS + AIFSN * slot, so AIFS = 3 slots with SIFS = 1 slot gives AIFSN = 2.
 *
 * Outputs (stdout, one CSV line):
 *   M,seed,S_ac3,S_ac1,D_ac3_ms,D_ac1_ms,n_ac3,n_ac1,associated
 *   S = normalized throughput (payload bits / time / 11 Mb/s), D = mean access delay.
 *   Access delay is measured per station and AC from the moment a frame becomes
 *   head-of-line (previous frame ACKed or dropped at the retry limit) until its ACK:
 *   under saturation the queue is never empty, so this is the paper's "first transmission
 *   attempt until successfully transmitted". Traffic starts at 2 s, after association;
 *   statistics start at 3 s.
 *   --delayCsv=<file> also dumps every access-delay sample (for the CDF of Fig. 8b).
 *
 * Run:  ./ns3 run "kong-edca --nSta=15 --seed=1"
 */
#include "ns3/core-module.h"
#include "ns3/mobility-module.h"
#include "ns3/network-module.h"
#include "ns3/wifi-module.h"

#include <fstream>
#include <map>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("A3KongEdca");

namespace
{
const uint8_t UP_AC3 = 6; // AC_VO
const uint8_t UP_AC1 = 1; // AC_BK
double g_warmup = 3.0;      // statistics start here
double g_trafficStart = 2.0; // all stations are associated well before this
uint64_t g_rxBytes[2] = {0, 0};                        // [AC3, AC1] at the AP
std::map<std::pair<uint32_t, int>, double> g_lastAck;  // (station, ac) -> time of last ACK
std::vector<double> g_delays[2];                       // access-delay samples (s)
std::ofstream g_delayCsv;
uint32_t g_assoc = 0;

int
AcOf(uint8_t tid)
{
    return (tid == UP_AC3 || tid == 7) ? 0 : 1;
}

void
OnRx(int ac, Ptr<const Packet> p, const Address&)
{
    if (Simulator::Now().GetSeconds() >= g_warmup)
    {
        g_rxBytes[ac] += p->GetSize();
    }
}

void
OnAcked(uint32_t sta, Ptr<const WifiMpdu> mpdu)
{
    if (!mpdu->GetHeader().IsQosData())
    {
        return;
    }
    int ac = AcOf(mpdu->GetHeader().GetQosTid());
    double now = Simulator::Now().GetSeconds();
    auto key = std::make_pair(sta, ac);
    auto it = g_lastAck.find(key);
    if (it != g_lastAck.end() && now >= g_warmup)
    {
        double d = now - it->second;
        g_delays[ac].push_back(d);
        if (g_delayCsv.is_open())
        {
            g_delayCsv << (ac == 0 ? "AC3" : "AC1") << "," << d * 1e3 << "\n";
        }
    }
    g_lastAck[key] = now;
}

void
OnDropped(uint32_t sta, WifiMacDropReason reason, Ptr<const WifiMpdu> mpdu)
{
    // a frame dropped at the retry limit frees the head of the queue: the next frame's
    // access delay starts now (paper: delay counts from the first transmission attempt)
    if (reason != WIFI_MAC_DROP_REACHED_RETRY_LIMIT || !mpdu->GetHeader().IsQosData())
    {
        return;
    }
    g_lastAck[std::make_pair(sta, AcOf(mpdu->GetHeader().GetQosTid()))] =
        Simulator::Now().GetSeconds();
}

void
OnAssoc(Mac48Address)
{
    g_assoc++;
}

void
ConfigureEdca(Ptr<NetDevice> dev, double sifsUs)
{
    auto wdev = DynamicCast<WifiNetDevice>(dev);
    wdev->GetPhy()->SetSifs(MicroSeconds(sifsUs));
    Ptr<WifiMac> mac = wdev->GetMac();
    PointerValue ptr;
    mac->GetAttribute("VO_Txop", ptr); // paper AC3
    auto vo = ptr.Get<QosTxop>();
    vo->SetMinCws({15});
    vo->SetMaxCws({127});
    vo->SetAifsns({2});
    vo->SetTxopLimits({Seconds(0)});
    mac->GetAttribute("BK_Txop", ptr); // paper AC1
    auto bk = ptr.Get<QosTxop>();
    bk->SetMinCws({31});
    bk->SetMaxCws({255});
    bk->SetAifsns({3});
    bk->SetTxopLimits({Seconds(0)});
}
} // namespace

int
main(int argc, char* argv[])
{
    uint32_t nSta = 15;
    uint32_t seed = 1;
    uint32_t payload = 1000;
    double simTime = 13.0; // includes association time and g_warmup
    double sifsUs = 20.0;  // Table I: SIFS = 1 time slot = 20 us
    double offeredMbps = 4.0;
    uint32_t retryLimit = 7; // not reported in the paper; ns-3 default
    std::string delayCsv;

    CommandLine cmd(__FILE__);
    cmd.AddValue("nSta", "Number of stations M", nSta);
    cmd.AddValue("seed", "RNG run number", seed);
    cmd.AddValue("payload", "Payload size (bytes)", payload);
    cmd.AddValue("simTime", "Simulated time incl. warm-up (s)", simTime);
    cmd.AddValue("warmup", "Statistics start time (s)", g_warmup);
    cmd.AddValue("trafficStart", "Traffic start time (s)", g_trafficStart);
    cmd.AddValue("sifsUs", "SIFS (us); Table I uses one 20 us slot", sifsUs);
    cmd.AddValue("offeredMbps", "Offered load per AC per station (Mb/s), saturating", offeredMbps);
    cmd.AddValue("retryLimit", "Frame retry limit", retryLimit);
    cmd.AddValue("delayCsv", "Dump access-delay samples to this CSV", delayCsv);
    cmd.Parse(argc, argv);

    RngSeedManager::SetSeed(1);
    RngSeedManager::SetRun(seed);
    if (!delayCsv.empty())
    {
        g_delayCsv.open(delayCsv);
        g_delayCsv << "ac,delay_ms\n";
    }

    NodeContainer ap;
    ap.Create(1);
    NodeContainer stas;
    stas.Create(nSta);

    YansWifiChannelHelper channel = YansWifiChannelHelper::Default();
    YansWifiPhyHelper phy;
    phy.SetChannel(channel.Create());

    WifiHelper wifi;
    wifi.SetStandard(WIFI_STANDARD_80211b);
    wifi.SetRemoteStationManager("ns3::ConstantRateWifiManager",
                                 "DataMode", StringValue("DsssRate11Mbps"),
                                 "ControlMode", StringValue("DsssRate11Mbps"),
                                 "RtsCtsThreshold", UintegerValue(0));

    WifiMacHelper mac;
    Ssid ssid("kong");
    mac.SetType("ns3::StaWifiMac", "Ssid", SsidValue(ssid), "QosSupported", BooleanValue(true),
                "FrameRetryLimit", UintegerValue(retryLimit));
    NetDeviceContainer staDevs = wifi.Install(phy, mac, stas);
    mac.SetType("ns3::ApWifiMac", "Ssid", SsidValue(ssid), "QosSupported", BooleanValue(true),
                "FrameRetryLimit", UintegerValue(retryLimit));
    NetDeviceContainer apDev = wifi.Install(phy, mac, ap);
    // the AP advertises its EDCA parameters; stations adopt them on association
    ConfigureEdca(apDev.Get(0), sifsUs);
    for (uint32_t i = 0; i < nSta; ++i)
    {
        ConfigureEdca(staDevs.Get(i), sifsUs);
    }

    MobilityHelper mobility;
    Ptr<ListPositionAllocator> pos = CreateObject<ListPositionAllocator>();
    pos->Add(Vector(0, 0, 0));
    for (uint32_t i = 0; i < nSta; ++i)
    {
        double a = 2 * M_PI * i / nSta;
        pos->Add(Vector(5 * std::cos(a), 5 * std::sin(a), 0));
    }
    mobility.SetPositionAllocator(pos);
    mobility.SetMobilityModel("ns3::ConstantPositionMobilityModel");
    mobility.Install(ap);
    mobility.Install(stas);

    PacketSocketHelper packetSocket;
    packetSocket.Install(ap);
    packetSocket.Install(stas);

    // one server per AC at the AP (protocol 1 = AC3, 2 = AC1)
    for (int ac = 0; ac < 2; ++ac)
    {
        PacketSocketAddress local;
        local.SetSingleDevice(apDev.Get(0)->GetIfIndex());
        local.SetProtocol(ac + 1);
        Ptr<PacketSocketServer> server = CreateObject<PacketSocketServer>();
        server->SetLocal(local);
        server->TraceConnectWithoutContext("Rx", MakeBoundCallback(&OnRx, ac));
        ap.Get(0)->AddApplication(server);
        server->SetStartTime(Seconds(0));
    }

    Time interval = Seconds(payload * 8.0 / (offeredMbps * 1e6));
    Ptr<UniformRandomVariable> jitter = CreateObject<UniformRandomVariable>();
    for (uint32_t i = 0; i < nSta; ++i)
    {
        for (int ac = 0; ac < 2; ++ac)
        {
            PacketSocketAddress remote;
            remote.SetSingleDevice(staDevs.Get(i)->GetIfIndex());
            remote.SetPhysicalAddress(apDev.Get(0)->GetAddress());
            remote.SetProtocol(ac + 1);
            Ptr<PacketSocketClient> client = CreateObject<PacketSocketClient>();
            client->SetRemote(remote);
            client->SetAttribute("PacketSize", UintegerValue(payload));
            client->SetAttribute("MaxPackets", UintegerValue(0));
            client->SetAttribute("Interval", TimeValue(interval));
            client->SetAttribute("Priority", UintegerValue(ac == 0 ? UP_AC3 : UP_AC1));
            stas.Get(i)->AddApplication(client);
            client->SetStartTime(Seconds(g_trafficStart + 0.1 * jitter->GetValue()));
        }
        auto wmac = DynamicCast<WifiNetDevice>(staDevs.Get(i))->GetMac();
        wmac->TraceConnectWithoutContext("AckedMpdu", MakeBoundCallback(&OnAcked, i));
        wmac->TraceConnectWithoutContext("DroppedMpdu", MakeBoundCallback(&OnDropped, i));
        wmac->TraceConnectWithoutContext("Assoc", MakeCallback(&OnAssoc));
    }

    Simulator::Stop(Seconds(simTime));
    Simulator::Run();

    double dur = simTime - g_warmup;
    double S[2];
    double D[2];
    for (int ac = 0; ac < 2; ++ac)
    {
        S[ac] = g_rxBytes[ac] * 8.0 / dur / 11e6;
        double sum = 0;
        for (double d : g_delays[ac])
        {
            sum += d;
        }
        D[ac] = g_delays[ac].empty() ? 0.0 : sum / g_delays[ac].size() * 1e3;
    }
    std::cout << "M,seed,S_ac3,S_ac1,D_ac3_ms,D_ac1_ms,n_ac3,n_ac1,associated\n"
              << nSta << "," << seed << "," << S[0] << "," << S[1] << "," << D[0] << "," << D[1]
              << "," << g_delays[0].size() << "," << g_delays[1].size() << "," << g_assoc
              << std::endl;

    Simulator::Destroy();
    return 0;
}
