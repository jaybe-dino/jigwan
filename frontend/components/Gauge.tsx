import type { CSSProperties } from "react";

export function Gauge({
  value,
  cls,
  size = 52,
}: {
  value: number;
  cls: string;
  size?: number;
}) {
  const style = { "--v": value, width: size, height: size } as CSSProperties;
  return <div className={`gring g-${cls}`} style={style} data-v={value} />;
}
