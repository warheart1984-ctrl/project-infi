import type { ReactNode } from "react";
import styles from "./Panel.module.css";

interface PanelProps {
  title: string;
  children: ReactNode;
  headerExtra?: ReactNode;
  className?: string;
}

export function Panel({ title, children, headerExtra, className }: PanelProps) {
  return (
    <section className={`${styles.panel} ${className ?? ""}`}>
      <header className={styles.header}>
        <h2>{title}</h2>
        {headerExtra}
      </header>
      <div className={styles.body}>{children}</div>
    </section>
  );
}
