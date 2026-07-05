export function ScoreSeal({ seal, size = 96 }: { seal: string; size?: number }) {
  return (
    <div className="seal-stamp" style={{ width: size, height: size }}>
      <span className="g" style={{ fontSize: seal.length > 1 ? size * 0.26 : size * 0.34 }}>
        {seal}
      </span>
      <span className="k" style={{ fontSize: size * 0.11 }}>
        地官
      </span>
    </div>
  );
}
