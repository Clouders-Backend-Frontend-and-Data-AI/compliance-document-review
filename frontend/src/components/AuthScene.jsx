// An illustrated dusk landscape for the auth pages: a stately institution on a lake,
// birds crossing the sky, drifting clouds, shimmering water and lit windows.
// All motion lives in auth-scene.css and switches off for reduced-motion users.

const BIRDS = [
  { x: 300, y: 300, s: 1.0, fly: 40, delay: -14, flap: 0.85 },
  { x: 420, y: 340, s: 0.75, fly: 46, delay: -30, flap: 0.7 },
  { x: 200, y: 262, s: 1.15, fly: 36, delay: -6, flap: 0.95 },
  { x: 600, y: 372, s: 0.6, fly: 52, delay: -40, flap: 0.65 },
  { x: 520, y: 296, s: 0.85, fly: 43, delay: -22, flap: 0.8 },
];

// [cx, cy, r, duration, delay]
const STARS = [
  [58, 60, 1.5, 4.2, 0],
  [122, 206, 1.2, 5, -1.5],
  [742, 96, 1.6, 3.8, -2],
  [700, 214, 1.2, 4.6, -0.5],
  [772, 40, 1.3, 5.2, -3],
  [30, 150, 1.1, 4, -1],
];

// [x, base y, height, lean, duration, delay]
const REEDS = [
  [26, 700, 70, -6, 4.2, -1],
  [44, 706, 92, 5, 3.6, -2],
  [68, 712, 64, -4, 4.8, -0.5],
  [96, 724, 80, 6, 4, -3],
  [124, 740, 56, -5, 3.4, -1.5],
  [778, 730, 66, 5, 4.4, -2],
  [756, 740, 84, -6, 3.8, -0.8],
  [732, 752, 58, 4, 4.6, -2.5],
];

// [x, y, width, duration, delay]
const SUN_GLINTS = [
  [520, 580, 70, 3.2, 0],
  [520, 596, 54, 3.8, -1],
  [520, 614, 82, 3.4, -2],
  [520, 634, 46, 4.2, -0.5],
  [520, 656, 66, 3.6, -1.5],
  [520, 682, 40, 4.4, -2.5],
];

const LAKE_GLINTS = [
  [140, 640, 60, 4.6, -1],
  [300, 610, 44, 5, -2],
  [640, 620, 56, 4.2, -0.5],
  [700, 690, 70, 5.2, -3],
  [380, 700, 50, 4.8, -1.8],
];

export function Bird({ x, y, s, fly, delay, flap }) {
  const wing = { fill: "none", stroke: "#2A2C48", strokeWidth: 2.4, strokeLinecap: "round" };
  return (
    <g
      className="scene-fly"
      style={{
        "--x0": `${-x - 140}px`,
        "--x1": `${940 - x}px`,
        "--fly": `${fly}s`,
        "--delay": `${delay}s`,
      }}
    >
      <g transform={`translate(${x} ${y}) scale(${s})`}>
        <path className="scene-wing-l" d="M0 0 Q-6 -6 -13 -1" style={{ "--flap": `${flap}s` }} {...wing} />
        <path className="scene-wing-r" d="M0 0 Q6 -6 13 -1" style={{ "--flap": `${flap}s` }} {...wing} />
        <circle r="1.8" fill="#2A2C48" />
      </g>
    </g>
  );
}

export default function AuthScene({ className = "" }) {
  return (
    <svg
      viewBox="0 0 800 800"
      preserveAspectRatio="xMidYMid slice"
      aria-hidden="true"
      className={`scene ${className}`}
    >
      <defs>
        <linearGradient id="sc-sky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#121C36" />
          <stop offset="0.22" stopColor="#24406E" />
          <stop offset="0.48" stopColor="#6B6597" />
          <stop offset="0.7" stopColor="#D48E7C" />
          <stop offset="0.88" stopColor="#F0B27A" />
          <stop offset="1" stopColor="#F6CB92" />
        </linearGradient>
        <radialGradient id="sc-sun-glow">
          <stop offset="0" stopColor="#FFDDA6" stopOpacity="0.85" />
          <stop offset="0.45" stopColor="#F7B27E" stopOpacity="0.35" />
          <stop offset="1" stopColor="#F7B27E" stopOpacity="0" />
        </radialGradient>
        <linearGradient id="sc-hill-far" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#8A98B4" />
          <stop offset="1" stopColor="#6F7F9D" />
        </linearGradient>
        <linearGradient id="sc-hill-mid" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#5F8A77" />
          <stop offset="1" stopColor="#3F6B5C" />
        </linearGradient>
        <linearGradient id="sc-ground" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#3C6A55" />
          <stop offset="1" stopColor="#25463A" />
        </linearGradient>
        <linearGradient id="sc-lake" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#EDB07C" />
          <stop offset="0.18" stopColor="#C18F93" />
          <stop offset="0.5" stopColor="#4D5F92" />
          <stop offset="1" stopColor="#1B2A4C" />
        </linearGradient>
        <linearGradient id="sc-haze" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#F3C08E" stopOpacity="0" />
          <stop offset="0.6" stopColor="#F3C08E" stopOpacity="0.32" />
          <stop offset="1" stopColor="#F3C08E" stopOpacity="0" />
        </linearGradient>
        <linearGradient id="sc-fade" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#fff" />
          <stop offset="1" stopColor="#000" />
        </linearGradient>
        <mask id="sc-reflect-mask" maskUnits="userSpaceOnUse" x="0" y="576" width="460" height="150">
          <rect x="0" y="576" width="460" height="150" fill="url(#sc-fade)" />
        </mask>
        <radialGradient id="sc-vignette" cx="0.5" cy="0.5" r="0.75">
          <stop offset="0.55" stopColor="#0A1428" stopOpacity="0" />
          <stop offset="1" stopColor="#0A1428" stopOpacity="0.4" />
        </radialGradient>
        <filter id="sc-grain" x="0" y="0" width="100%" height="100%">
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch" />
          <feColorMatrix type="saturate" values="0" />
        </filter>
      </defs>

      {/* Sky */}
      <rect width="800" height="580" fill="url(#sc-sky)" />
      {STARS.map(([cx, cy, r, dur, delay]) => (
        <circle
          key={`${cx}-${cy}`}
          className="scene-star"
          cx={cx}
          cy={cy}
          r={r}
          fill="#FFF4DC"
          style={{ "--dur": `${dur}s`, "--delay": `${delay}s` }}
        />
      ))}

      {/* Sun */}
      <circle className="scene-glow" cx="520" cy="470" r="190" fill="url(#sc-sun-glow)" />
      <circle cx="520" cy="470" r="38" fill="#FFE6B0" />

      {/* Clouds */}
      <g className="scene-drift" style={{ "--dur": "56s" }}>
        <g transform="translate(170 318)" fill="#F4C7B0" opacity="0.38">
          <ellipse rx="64" ry="9" />
          <ellipse cx="34" cy="-7" rx="38" ry="8" />
          <ellipse cx="-38" cy="5" rx="34" ry="7" />
        </g>
      </g>
      <g className="scene-drift" style={{ "--dur": "64s", "--delay": "-20s" }}>
        <g transform="translate(590 250)" fill="#C9B6D6" opacity="0.3">
          <ellipse rx="70" ry="9" />
          <ellipse cx="-30" cy="-7" rx="40" ry="8" />
          <ellipse cx="42" cy="5" rx="34" ry="7" />
        </g>
      </g>
      <g className="scene-drift" style={{ "--dur": "72s", "--delay": "-35s" }}>
        <g transform="translate(400 410)" fill="#F8D2A8" opacity="0.35">
          <ellipse rx="52" ry="7" />
          <ellipse cx="26" cy="-5" rx="30" ry="6" />
        </g>
      </g>

      {/* Distant mountains and hills */}
      <path d="M560 480 L640 402 L690 440 L740 396 L800 450 L800 490 L560 490 Z" fill="#8E7F9E" />
      <path
        d="M0 505 C70 478 150 486 230 494 S360 476 440 488 S560 462 640 452 S740 458 800 470 L800 575 L0 575 Z"
        fill="url(#sc-hill-far)"
      />
      <path
        d="M0 528 C90 506 190 522 290 530 S470 514 560 500 S720 500 800 512 L800 580 L0 580 Z"
        fill="url(#sc-hill-mid)"
      />

      {/* Lake */}
      <rect y="566" width="800" height="234" fill="url(#sc-lake)" />
      <rect y="566" width="800" height="2" fill="#FFE0B0" opacity="0.5" />
      {SUN_GLINTS.map(([x, y, w, dur, delay]) => (
        <rect
          key={y}
          className="scene-shimmer"
          x={x - w / 2}
          y={y}
          width={w}
          height="3"
          rx="1.5"
          fill="#FFE7B8"
          style={{ "--dur": `${dur}s`, "--delay": `${delay}s` }}
        />
      ))}
      {LAKE_GLINTS.map(([x, y, w, dur, delay]) => (
        <rect
          key={`${x}-${y}`}
          className="scene-shimmer"
          x={x - w / 2}
          y={y}
          width={w}
          height="2"
          rx="1"
          fill="#DCE4FF"
          style={{ "--dur": `${dur}s`, "--delay": `${delay}s` }}
        />
      ))}
      <g mask="url(#sc-reflect-mask)" opacity="0.24">
        <use href="#sc-villa" transform="translate(0 1136) scale(1 -1)" />
      </g>
      <rect y="520" width="800" height="60" fill="url(#sc-haze)" />

      {/* Shore */}
      <path
        d="M0 552 C80 545 170 556 250 557 S380 552 440 560 C470 566 466 576 420 576 L0 576 Z"
        fill="url(#sc-ground)"
      />

      {/* The institution */}
      <g id="sc-villa">
        <rect x="84" y="506" width="46" height="54" fill="#DDB894" />
        <rect x="290" y="506" width="46" height="54" fill="#D3AA86" />
        <polygon points="78,506 107,488 136,506" fill="#B85C3E" />
        <polygon points="284,506 313,488 342,506" fill="#A9523A" />
        <rect x="130" y="478" width="160" height="82" fill="#E8C7A4" />
        <polygon points="122,478 210,436 298,478" fill="#B85C3E" />
        <polygon points="140,476 210,442 280,476" fill="#C9694A" />
        <rect x="126" y="474" width="168" height="6" fill="#F3DDC2" />
        <rect x="124" y="548" width="172" height="6" fill="#EAD3B8" />
        <rect x="118" y="554" width="184" height="6" fill="#DDBF9F" />

        {[158, 182, 230, 254].map((x, i) => (
          <rect
            key={x}
            className="scene-window"
            x={x}
            y="500"
            width="8"
            height="26"
            fill="#F7C56E"
            style={{ "--dur": `${5 + i}s`, "--delay": `${-i * 1.3}s` }}
          />
        ))}
        <path
          className="scene-window"
          d="M203 548 V522 Q210 508 217 522 V548 Z"
          fill="#FBD283"
          style={{ "--dur": "7s", "--delay": "-2s" }}
        />
        {[146, 170, 194, 218, 242, 266].map((x) => (
          <rect key={x} x={x} y="482" width="8" height="66" fill="#F6E6CF" />
        ))}

        {[92, 112].map((x, i) => (
          <rect
            key={x}
            className="scene-window"
            x={x}
            y="522"
            width="12"
            height="18"
            fill="#F7C56E"
            style={{ "--dur": `${6 + i}s`, "--delay": `${-i * 2}s` }}
          />
        ))}
        {[298, 318].map((x, i) => (
          <rect
            key={x}
            className="scene-window"
            x={x}
            y="522"
            width="12"
            height="18"
            fill="#F7C56E"
            style={{ "--dur": `${5.5 + i}s`, "--delay": `${-1 - i * 1.7}s` }}
          />
        ))}
      </g>

      {/* Cypress trees */}
      <g fill="#1D3B33">
        <ellipse cx="52" cy="522" rx="9" ry="36" />
        <ellipse cx="70" cy="530" rx="8" ry="28" />
        <ellipse cx="352" cy="524" rx="9" ry="34" />
        <ellipse cx="372" cy="532" rx="8" ry="26" />
        <ellipse cx="398" cy="540" rx="7" ry="20" />
      </g>

      {/* Birds */}
      {BIRDS.map((b) => (
        <Bird key={`${b.x}-${b.y}`} {...b} />
      ))}

      {/* Foreground banks and reeds */}
      <path d="M0 800 L0 686 C58 682 130 712 196 800 Z" fill="#14302A" />
      <path d="M800 800 L800 716 C748 724 706 756 684 800 Z" fill="#14302A" />
      {REEDS.map(([x, y, h, lean, dur, delay]) => (
        <path
          key={x}
          className="scene-reed"
          d={`M${x} ${y} Q${x + lean * 0.2} ${y - h * 0.55} ${x + lean} ${y - h}`}
          fill="none"
          stroke="#14302A"
          strokeWidth="3"
          strokeLinecap="round"
          style={{ "--dur": `${dur}s`, "--delay": `${delay}s` }}
        />
      ))}

      {/* Depth and texture */}
      <rect width="800" height="800" fill="url(#sc-vignette)" />
      <rect
        width="800"
        height="800"
        filter="url(#sc-grain)"
        opacity="0.08"
        style={{ mixBlendMode: "overlay" }}
      />
    </svg>
  );
}
