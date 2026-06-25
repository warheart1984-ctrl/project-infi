import styles from "./flightDeck.module.css";
import { AgentSelector } from "./AgentSelector";
import { ClusterMap } from "./ClusterMap";
import { KernelStatusRail } from "./KernelStatusRail";
import { ClusterTimeline } from "./ClusterTimeline";

export function FlightDeckShell() {
  return (
    <div className={styles.flightShell}>
      <div className={styles.left}>
        <AgentSelector />
      </div>
      <div className={styles.center}>
        <ClusterMap />
      </div>
      <div className={styles.right}>
        <KernelStatusRail />
      </div>
      <div className={styles.bottom}>
        <ClusterTimeline />
      </div>
    </div>
  );
}
