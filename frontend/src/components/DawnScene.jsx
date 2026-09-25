// A dawn scene for the signup page: sun rising between the towers of a suspension
// bridge, a city on the far shore, sailboats on the river and birds in the sky.
// Motion comes from auth-scene.css and switches off for reduced-motion users.
import { Bird } from "./AuthScene";

const HORIZON = 580;

const BIRDS = [
  { x: 250, y: 330, s: 1.0, fly: 42, delay: -10, flap: 0.85 },
  { x: 420, y: 372, s: 0.7, fly: 50, delay: -28, flap: 0.7 },
  { x: 560, y: 312, s: 1.1, fly: 38, delay: -20, flap: 0.95 },
  { x: 150, y: 402, s: 0.6, fly: 55, delay: -38, flap: 0.65 },
];

// [x, width, height, "spire"?]
const FAR_LEFT = [[6, 26, 60], [36, 20, 92], [60, 30, 70], [96, 18, 112], [118, 28, 64], [150, 22, 84], [176, 26, 52]];
const NEAR_LEFT = [[0, 34, 84], [38, 24, 128], [66, 32, 96], [102, 22, 150, "spire"], [128, 30, 104], [162, 26, 78]];
const FAR_RIGHT = [[600, 26, 72], [630, 22, 100], [656, 30, 64], [690, 20, 120], [714, 28, 80], [746, 24, 96], [774, 26, 58]];
const NEAR_RIGHT = [[604, 30, 90], [638, 24, 140], [666, 34, 102], [704, 22, 160, "spire"], [730, 30, 110], [764, 36, 84]];

const SUN_GLINTS = [
  [588, 80, 3.2, 0],
  [602, 60, 3.8, -1],
  [620, 92, 3.4, -2],
  [640, 50, 4.2, -0.5],
  [662, 74, 3.6, -1.5],
  [690, 46, 4.4, -2.5],
];

const GRASS = [
  [20, 704, 40, -5, 4.2, -1],
  [40, 700, 52, 4, 3.6, -2],
  [62, 708, 36, -4, 4.8, -0.5],
  [84, 716, 44, 5, 4, -3],
  [760, 734, 34, -4, 4.4, -1.4],
  [780, 730, 46, 5, 3.8, -2.2],
];

const RAYS = Array.from({ length: 16 }, (_, i) => {
  const a = (i * 22.5 * Math.PI) / 180;
  const w = (3.4 * Math.PI) / 180;
  const p = (t) => [400 + 520 * Math.sin(t), 552 - 520 * Math.cos(t)];
  const [x1, y1] = p(a - w);
  const [x2, y2] = p(a + w);
  return `M400 552 L${x1.toFixed(1)} ${y1.toFixed(1)} L${x2.toFixed(1)} ${y2.toFixed(1)} Z`;
}).join(" ");

// Points along the main suspension cable, for the vertical hangers.
const cableY = (x) => {
  const t = (x - 250) / 300;
  return (1 - t) * (1 - t) * 440 + 2 * (1 - t) * t * 640 + t * t * 440;
};
const HANGERS = Array.from({ length: 14 }, (_, i) => 270 + i * 20);

function Skyline({ items, fill }) {
  return items.map(([x, w, h, spire]) => (
    <g key={`${x}-${h}`} fill={fill}>
      <rect x={x} y={HORIZON - h} width={w} height={h} />
      {spire && <polygon points={`${x + w / 2 - 3},${HORIZON - h} ${x + w / 2},${HORIZON - h - 24} ${x + w / 2 + 3},${HORIZON - h}`} />}
    </g>
  ));
}

function LitWindows({ items }) {
  const out = [];
  items.forEach(([x, w, h], i) => {
    const cols = Math.floor((w - 6) / 8);
    const rows = Math.floor((h - 10) / 14);
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        if ((i * 5 + r * 3 + c * 7) % 4 !== 0) continue;
        const animated = (r + c + i) % 5 === 0;
        out.push(
          <rect
            key={`${x}-${r}-${c}`}
            className={animated ? "scene-window" : undefined}
            x={x + 5 + c * 8}
            y={HORIZON - h + 8 + r * 14}
            width="4"
            height="6"
            fill="#FFE2A0"
            style={animated ? { "--dur": `${5 + ((r + c) % 4)}s`, "--delay": `${-(r + i)}s` } : undefined}
          />
        );
      }
    }
  });
  return out;
}

function Sailboat({ x, y, s, fly, delay, bob }) {
  return (
    <g
      className="scene-fly"
      style={{
        "--x0": `${-x - 90}px`,
        "--x1": `${900 - x}px`,
        "--dy": "0px",
        "--fly": `${fly}s`,
        "--delay": `${delay}s`,
      }}
    >
      <g transform={`translate(${x} ${y}) scale(${s})`}>
        <g className="scene-bob" style={{ "--dur": `${bob}s` }}>
          <line x1="0" y1="-38" x2="0" y2="0" stroke="#22406C" strokeWidth="1.4" />
          <path d="M-1.5 -36 L-1.5 -4 L-16 -4 Z" fill="#FFF3DE" />
          <path d="M2 -30 L2 -4 L15 -4 Z" fill="#F6D9B6" />
          <path d="M-18 0 L18 0 L12 7 L-12 7 Z" fill="#24406E" />
        </g>
      </g>
    </g>
  );
}

export default function DawnScene({ className = "" }) {
  return (
    <svg
      viewBox="0 0 800 800"
      preserveAspectRatio="xMidYMid slice"
      aria-hidden="true"
      className={`scene ${className}`}
    >
      <defs>
        <linearGradient id="dw-sky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#27508A" />
          <stop offset="0.3" stopColor="#5E88B8" />
          <stop offset="0.55" stopColor="#B9A9C9" />
          <stop offset="0.75" stopColor="#F4B6A0" />
          <stop offset="0.9" stopColor="#FBD9A3" />
          <stop offset="1" stopColor="#FFE9BC" />
        </linearGradient>
        <radialGradient id="dw-sun-glow">
          <stop offset="0" stopColor="#FFF0C4" stopOpacity="0.95" />
          <stop offset="0.4" stopColor="#FFCB8E" stopOpacity="0.4" />
          <stop offset="1" stopColor="#FFCB8E" stopOpacity="0" />
        </radialGradient>
        <radialGradient id="dw-rays" gradientUnits="userSpaceOnUse" cx="400" cy="552" r="520">
          <stop offset="0" stopColor="#FFF3D2" stopOpacity="0.4" />
          <stop offset="1" stopColor="#FFF3D2" stopOpacity="0" />
        </radialGradient>
        <linearGradient id="dw-river" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#FFD9A0" />
          <stop offset="0.18" stopColor="#F2B9A0" />
          <stop offset="0.5" stopColor="#7A98BE" />
          <stop offset="1" stopColor="#22406C" />
        </linearGradient>
        <linearGradient id="dw-mist" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#FFE3B8" stopOpacity="0" />
          <stop offset="0.6" stopColor="#FFE3B8" stopOpacity="0.4" />
          <stop offset="1" stopColor="#FFE3B8" stopOpacity="0" />
        </linearGradient>
        <radialGradient id="dw-lamp">
          <stop offset="0" stopColor="#FFDDA6" stopOpacity="0.55" />
          <stop offset="1" stopColor="#FFDDA6" stopOpacity="0" />
        </radialGradient>
        <radialGradient id="dw-vignette" cx="0.5" cy="0.5" r="0.75">
          <stop offset="0.55" stopColor="#0A1428" stopOpacity="0" />
          <stop offset="1" stopColor="#0A1428" stopOpacity="0.35" />
        </radialGradient>
        <filter id="dw-grain" x="0" y="0" width="100%" height="100%">
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch" />
          <feColorMatrix type="saturate" values="0" />
        </filter>
      </defs>

      {/* Sky */}
      <rect width="800" height={HORIZON + 2} fill="url(#dw-sky)" />
      <circle className="scene-glow" cx="400" cy="552" r="240" fill="url(#dw-sun-glow)" />
      <path className="scene-rays" d={RAYS} fill="url(#dw-rays)" />
      <circle cx="400" cy="552" r="44" fill="#FFF0C4" />

      {/* Clouds */}
      <g className="scene-drift" style={{ "--dur": "60s" }}>
        <g transform="translate(180 300)" fill="#FFF0E0" opacity="0.35">
          <ellipse rx="70" ry="8" />
          <ellipse cx="36" cy="-6" rx="42" ry="7" />
          <ellipse cx="-40" cy="5" rx="36" ry="6" />
        </g>
      </g>
      <g className="scene-drift" style={{ "--dur": "68s", "--delay": "-25s" }}>
        <g transform="translate(610 262)" fill="#E4D2E8" opacity="0.32">
          <ellipse rx="66" ry="8" />
          <ellipse cx="-30" cy="-6" rx="38" ry="7" />
        </g>
      </g>
      <g className="scene-drift" style={{ "--dur": "76s", "--delay": "-40s" }}>
        <g transform="translate(330 452)" fill="#FFE6C4" opacity="0.4">
          <ellipse rx="56" ry="6" />
          <ellipse cx="28" cy="-4" rx="30" ry="5" />
        </g>
      </g>

      {/* City on the far shore */}
      <Skyline items={FAR_LEFT} fill="#9AA9C9" />
      <Skyline items={FAR_RIGHT} fill="#9AA9C9" />
      <Skyline items={NEAR_LEFT} fill="#3F5C8C" />
      <Skyline items={NEAR_RIGHT} fill="#3F5C8C" />
      <LitWindows items={NEAR_LEFT} />
      <LitWindows items={NEAR_RIGHT} />
      <rect y={HORIZON - 3} width="800" height="6" fill="#3A5583" />

      {/* River */}
      <rect y={HORIZON} width="800" height={800 - HORIZON} fill="url(#dw-river)" />
      {SUN_GLINTS.map(([y, w, dur, delay]) => (
        <rect
          key={y}
          className="scene-shimmer"
          x={400 - w / 2}
          y={y}
          width={w}
          height="3"
          rx="1.5"
          fill="#FFF3D2"
          style={{ "--dur": `${dur}s`, "--delay": `${delay}s` }}
        />
      ))}
      <rect y="540" width="800" height="70" fill="url(#dw-mist)" />

      <Sailboat x={180} y={650} s={1.1} fly={110} delay={-30} bob={4.2} />
      <Sailboat x={620} y={628} s={0.7} fly={95} delay={-10} bob={3.6} />
      <Sailboat x={520} y={716} s={1.5} fly={140} delay={-90} bob={4.8} />

      {/* Suspension bridge */}
      <g stroke="#1B3358" fill="none">
        <path d="M250 440 Q400 640 550 440" strokeWidth="2.4" />
        <path d="M250 440 L0 592" strokeWidth="2" />
        <path d="M550 440 L800 592" strokeWidth="2" />
        <g strokeWidth="1.2" opacity="0.8">
          {HANGERS.map((x) => (
            <line key={x} x1={x} y1={cableY(x)} x2={x} y2="598" />
          ))}
        </g>
      </g>
      <g fill="#1B3358">
        <rect x="242" y="438" width="6" height="168" />
        <rect x="252" y="438" width="6" height="168" />
        <rect x="242" y="462" width="16" height="5" />
        <rect x="242" y="500" width="16" height="5" />
        <rect x="242" y="540" width="16" height="5" />
        <rect x="542" y="438" width="6" height="168" />
        <rect x="552" y="438" width="6" height="168" />
        <rect x="542" y="462" width="16" height="5" />
        <rect x="542" y="500" width="16" height="5" />
        <rect x="542" y="540" width="16" height="5" />
        <rect y="598" width="800" height="8" />
      </g>
      <rect y="606" width="800" height="3" fill="#14263F" opacity="0.35" />
      {Array.from({ length: 20 }, (_, i) => (
        <circle
          key={i}
          className="scene-window"
          cx={20 + i * 40}
          cy="594"
          r="1.7"
          fill="#FFE2A0"
          style={{ "--dur": `${5 + (i % 4)}s`, "--delay": `${-i * 0.7}s` }}
        />
      ))}

      {/* Birds */}
      {BIRDS.map((b) => (
        <Bird key={`${b.x}-${b.y}`} {...b} />
      ))}

      {/* Foreground banks, grass and lamp */}
      <path d="M0 800 L0 700 C70 690 150 720 210 800 Z" fill="#163A3A" />
      <circle cx="26" cy="702" r="24" fill="#1D4A44" />
      <circle cx="62" cy="710" r="19" fill="#1D4A44" />
      <circle cx="98" cy="726" r="14" fill="#1D4A44" />
      <path d="M800 800 L800 730 C760 728 720 752 700 800 Z" fill="#163A3A" />
      <circle cx="746" cy="676" r="34" fill="url(#dw-lamp)" />
      <rect x="744" y="686" width="5" height="114" fill="#1B2A44" />
      <circle className="scene-window" cx="746.5" cy="682" r="7" fill="#FFE2A0" style={{ "--dur": "8s" }} />
      {GRASS.map(([x, y, h, lean, dur, delay]) => (
        <path
          key={x}
          className="scene-reed"
          d={`M${x} ${y} Q${x + lean * 0.2} ${y - h * 0.55} ${x + lean} ${y - h}`}
          fill="none"
          stroke="#163A3A"
          strokeWidth="3"
          strokeLinecap="round"
          style={{ "--dur": `${dur}s`, "--delay": `${delay}s` }}
        />
      ))}

      {/* Depth and texture */}
      <rect width="800" height="800" fill="url(#dw-vignette)" />
      <rect
        width="800"
        height="800"
        filter="url(#dw-grain)"
        opacity="0.08"
        style={{ mixBlendMode: "overlay" }}
      />
    </svg>
  );
}
