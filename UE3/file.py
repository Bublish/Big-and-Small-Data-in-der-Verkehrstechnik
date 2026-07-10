import os
import sys
import random
from sumolib import checkBinary  # noqa
import traci  # noqa

# Sumo Tools
if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    sys.path.append(tools)
else:
    sys.exit("No SUMO environment defined (SUMO_HOME missing). ")


def generate_routefiles():
    random.seed(42)  # make tests reproducible
    N = 3600
    pWo = 0.5  
    pOW = 0.5 
    pNS = 0.02

    with open("TT1.rou.xml", "w") as routes:
        print(
            """<routes>
        <vType id="typeWO" accel="0.8" decel="4.5" sigma="0.5" length="5" minGap="2.5" maxSpeed="16.27" departSpeed="16.27" guiShape="passenger"/>
        <vType id="typeNS" accel="0.8" decel="4.5" sigma="0.5" length="7" minGap="3" maxSpeed="25" departSpeed="25" guiShape="emergency"/>
        <route id="rnl" edges="-E1 -E0" />
        <route id="lnr" edges="E0 E1" />
        <route id="nns" edges="E2 E3" />"""     
        ,file=routes,)

        vehNr = 0
        for i in range(N):
            if random.uniform(0, 1) < pWo:
                print(
                    '    <vehicle id="nachLinks_%i" type="typeWO" route="lnr" depart="%i" />'
                    % (vehNr, i),
                    file=routes,
                )
                vehNr += 1

            if random.uniform(0, 1) < pOW:
                print(
                    '    <vehicle id="nachRechts_%i" type="typeWO" route="rnl" depart="%i" />'
                    % (vehNr, i),
                    file=routes,
                )
                vehNr += 1

            if random.uniform(0, 1) < pNS:
                print(
                    '    <vehicle id="down_%i" type="typeNS" route="nns" depart="%i" color="1,0,0"/>'
                    % (vehNr, i),
                    file=routes,
                )
                vehNr += 1
            
        print("</routes>", file=routes)

def run_minmal(steps: int = 200):
    for _ in range(steps):
        traci.simulationStep()

def run_with_tls_control():
    step = 0
    waiting = {} # vehID -> WaitingTimeSeconds

    #start with phase 2
    traci.trafficlight.setPhase("J1", 2)

    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()

        for vid in traci.vehicle.getIDList():
            wt = traci.vehicle.getAccumulatedWaitingTime(vid)
            waiting[vid] = max(waiting.get(vid, 0.0), wt)
        
        if traci.trafficlight.getPhase("J1") == 2:
            if traci.inductionloop.getLastStepVehicleNumber("e1_0") > 0:
                traci.trafficlight.setPhase("J1", 3)
            else:
                traci.trafficlight.setPhase("J1", 2)

        step += 1
    #write individual waiting times to XML
    with open("waitingTimes.xml", "w", encoding="utf-8") as f:
        f.write("<waitingTimes>\n")
        for vid, wt in sorted(waiting.items()):
            f.write(f'  <vehicle id="{vid}" waitingTime="{wt:.1f}"/>\n')
        f.write("</waitingTimes>\n")

    #average waiting time
    avg_waiting_time = sum(waiting.values()) / len(waiting) if waiting else 0
    print(f"Average waiting time: {avg_waiting_time:.2f} seconds")

    traci.close()
    sys.stdout.flush()
    

if __name__ == "__main__":
    generate_routefiles()

    # choose GUI or console:
    # sumoBinary = checkBinary("sumo")
    sumoBinary = checkBinary("sumo-gui")

    traci.start([sumoBinary, "-c", "TT1.sumocfg","--start", "--quit-on-end"])
    run_with_tls_control()