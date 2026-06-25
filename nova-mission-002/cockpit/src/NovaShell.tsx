import styles from "./NovaShell.module.css";
import { TopBar } from "./layout/TopBar";
import { LeftRail } from "./layout/LeftRail";
import { RightRail } from "./layout/RightRail";
import { CenterCanvas } from "./layout/CenterCanvas";
import { BottomBand } from "./layout/BottomBand";

export function NovaShell() {
  return (
    <div className={styles.shell}>
      <TopBar />
      <div className={styles.main}>
        <LeftRail />
        <CenterCanvas />
        <RightRail />
      </div>
      <BottomBand />
    </div>
  );
}
