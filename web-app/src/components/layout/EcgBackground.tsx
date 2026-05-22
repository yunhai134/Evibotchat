const ECG_PERIOD = 600

const ECG_PATH = [
  "M 0 50",
  "L 100 50",
  "L 110 50",
  "L 112 40",
  "L 114 50",
  "L 120 50",
  "L 124 20",
  "L 128 80",
  "L 132 50",
  "L 140 50",
  "L 160 50",
  "L 165 50",
  "L 168 35",
  "L 171 50",
  "L 175 50",
  "L 178 42",
  "L 181 50",
  "L 185 50",
  "L 190 50",
  "L 210 50",
  "L 220 50",
  "L 222 45",
  "L 224 50",
  "L 230 50",
  "L 235 48",
  "L 238 50",
  "L 245 50",
  "L 250 50",
  "L 260 50",
  "L 270 50",
  "L 275 50",
  "L 278 46",
  "L 281 50",
  `L ${ECG_PERIOD} 50`,
].join("\n")

const THIN_PATH = [
  "M 0 50",
  "L 80 50",
  "L 90 50",
  "L 92 42",
  "L 94 50",
  "L 100 50",
  "L 104 28",
  "L 108 72",
  "L 112 50",
  "L 120 50",
  "L 140 50",
  "L 145 50",
  "L 148 38",
  "L 151 50",
  "L 155 50",
  "L 158 44",
  "L 161 50",
  "L 165 50",
  "L 170 50",
  "L 190 50",
  "L 200 50",
  "L 202 46",
  "L 204 50",
  "L 210 50",
  "L 215 48",
  "L 218 50",
  "L 225 50",
  "L 230 50",
  `L ${ECG_PERIOD} 50`,
].join("\n")

const Faint_PATH = [
  "M 0 50",
  "L 100 50",
  "L 108 50",
  "L 110 44",
  "L 112 50",
  "L 118 50",
  "L 122 32",
  "L 126 68",
  "L 130 50",
  "L 138 50",
  "L 150 50",
  "L 154 50",
  "L 156 42",
  "L 158 50",
  "L 162 50",
  "L 165 46",
  "L 168 50",
  "L 172 50",
  "L 178 50",
  "L 195 50",
  `L ${ECG_PERIOD} 50`,
].join("\n")

const layers = [
  {
    path: ECG_PATH,
    top: 20,
    speed: 10,
    stroke: "3",
    opacity: 0.55,
    glowBlur: 16,
    glowOpacity: 0.55,
    isMain: true,
  },
  {
    path: THIN_PATH,
    top: 38,
    speed: 14,
    stroke: "2",
    opacity: 0.35,
    glowBlur: 10,
    glowOpacity: 0.35,
    isMain: false,
  },
  {
    path: Faint_PATH,
    top: 56,
    speed: 20,
    stroke: "1.5",
    opacity: 0.2,
    glowBlur: 6,
    glowOpacity: 0.2,
    isMain: false,
  },
  {
    path: ECG_PATH,
    top: 74,
    speed: 28,
    stroke: "1",
    opacity: 0.1,
    glowBlur: 4,
    glowOpacity: 0.1,
    isMain: false,
  },
]

export function EcgBackground() {
  return (
    <div
      aria-hidden="true"
      className="fixed inset-0 pointer-events-none z-0 overflow-hidden"
    >
      <style>{`
        @keyframes ecg-scroll {
          from { transform: translateX(0); }
          to { transform: translateX(-50%); }
        }
        @keyframes glass-shimmer {
          0%, 100% { transform: translateX(-100%) rotate(15deg); }
          50% { transform: translateX(200%) rotate(15deg); }
        }
        @keyframes iridescent-float {
          0%, 100% { transform: translate(0, 0) scale(1); opacity: 0.3; }
          25% { transform: translate(30px, -20px) scale(1.05); opacity: 0.4; }
          50% { transform: translate(-10px, 30px) scale(0.95); opacity: 0.25; }
          75% { transform: translate(20px, 10px) scale(1.02); opacity: 0.35; }
        }
        @keyframes iridescent-float-2 {
          0%, 100% { transform: translate(0, 0) scale(1); opacity: 0.2; }
          25% { transform: translate(-20px, 15px) scale(0.95); opacity: 0.3; }
          50% { transform: translate(30px, -10px) scale(1.05); opacity: 0.15; }
          75% { transform: translate(-10px, -20px) scale(1.02); opacity: 0.25; }
        }
        @keyframes glass-edge-glow {
          0%, 100% { opacity: 0.3; }
          50% { opacity: 0.6; }
        }
        .ecg-scrolling { animation: ecg-scroll linear infinite; will-change: transform; }
        .glass-shimmer { animation: glass-shimmer 8s ease-in-out infinite; }
        .iridescent-float { animation: iridescent-float 12s ease-in-out infinite; }
        .iridescent-float-2 { animation: iridescent-float-2 15s ease-in-out infinite; }
        .glass-edge-glow { animation: glass-edge-glow 4s ease-in-out infinite; }
        @media (prefers-reduced-motion: reduce) {
          .ecg-scrolling, .glass-shimmer, .iridescent-float, .iridescent-float-2, .glass-edge-glow { animation: none; }
        }
      `}</style>

      {/* Base background - white in light, dark navy in dark */}
      <div className="absolute inset-0 bg-white dark:bg-[#041020]" />

      {/* Iridescent gradient orbs - light refraction through glass */}
      <div
        className="absolute iridescent-float"
        style={{
          top: "10%",
          left: "5%",
          width: "45%",
          height: "55%",
          background: "radial-gradient(ellipse at 40% 50%, rgba(180,220,255,0.35) 0%, rgba(200,180,255,0.15) 40%, transparent 70%)",
          filter: "blur(60px)",
          willChange: "transform, opacity",
        }}
      />
      <div
        className="absolute iridescent-float-2 dark:hidden"
        style={{
          top: "30%",
          right: "0%",
          width: "50%",
          height: "60%",
          background: "radial-gradient(ellipse at 60% 50%, rgba(255,200,220,0.2) 0%, rgba(180,210,255,0.2) 35%, rgba(200,230,200,0.1) 60%, transparent 80%)",
          filter: "blur(70px)",
          willChange: "transform, opacity",
        }}
      />
      <div
        className="absolute hidden dark:block"
        style={{
          top: "30%",
          right: "0%",
          width: "50%",
          height: "60%",
          background: "radial-gradient(ellipse at 60% 50%, rgba(0,100,180,0.25) 0%, rgba(0,80,160,0.15) 35%, rgba(0,60,120,0.08) 60%, transparent 80%)",
          filter: "blur(70px)",
          willChange: "transform, opacity",
        }}
      />
      <div
        className="absolute dark:hidden"
        style={{
          top: "55%",
          left: "20%",
          width: "35%",
          height: "40%",
          background: "radial-gradient(ellipse at 50% 50%, rgba(210,230,255,0.2) 0%, rgba(230,210,255,0.1) 40%, transparent 70%)",
          filter: "blur(80px)",
        }}
      />
      <div
        className="absolute hidden dark:block"
        style={{
          top: "55%",
          left: "20%",
          width: "35%",
          height: "40%",
          background: "radial-gradient(ellipse at 50% 50%, rgba(0,80,150,0.18) 0%, rgba(0,60,120,0.08) 40%, transparent 70%)",
          filter: "blur(80px)",
        }}
      />

      {/* Glass surface reflection streak */}
      <div
        className="absolute inset-0 glass-shimmer pointer-events-none dark:hidden"
        style={{
          background: "linear-gradient(to right, transparent 0%, rgba(255,255,255,0.6) 20%, rgba(255,255,255,0.8) 30%, rgba(200,220,255,0.3) 40%, transparent 60%)",
          filter: "blur(40px)",
          width: "200%",
          height: "200%",
          marginLeft: "-50%",
          marginTop: "-50%",
        }}
      />
      <div
        className="absolute inset-0 glass-shimmer pointer-events-none hidden dark:block"
        style={{
          background: "linear-gradient(to right, transparent 0%, rgba(0,140,255,0.15) 20%, rgba(0,180,255,0.25) 30%, rgba(0,100,200,0.1) 40%, transparent 60%)",
          filter: "blur(40px)",
          width: "200%",
          height: "200%",
          marginLeft: "-50%",
          marginTop: "-50%",
        }}
      />

      {/* Glass edge highlight - top */}
      <div
        className="absolute top-0 left-0 right-0 h-px glass-edge-glow dark:hidden"
        style={{
          background: "linear-gradient(90deg, transparent 0%, rgba(180,200,255,0.5) 30%, rgba(255,255,255,0.8) 50%, rgba(180,200,255,0.5) 70%, transparent 100%)",
        }}
      />
      <div
        className="absolute top-0 left-0 right-0 h-px glass-edge-glow hidden dark:block"
        style={{
          background: "linear-gradient(90deg, transparent 0%, rgba(0,120,200,0.3) 30%, rgba(0,180,255,0.5) 50%, rgba(0,120,200,0.3) 70%, transparent 100%)",
        }}
      />

      {/* Glass edge highlight - bottom */}
      <div
        className="absolute bottom-0 left-0 right-0 h-px glass-edge-glow dark:hidden"
        style={{
          background: "linear-gradient(90deg, transparent 0%, rgba(180,200,255,0.3) 30%, rgba(255,255,255,0.6) 50%, rgba(180,200,255,0.3) 70%, transparent 100%)",
          animationDelay: "2s",
        }}
      />
      <div
        className="absolute bottom-0 left-0 right-0 h-px glass-edge-glow hidden dark:block"
        style={{
          background: "linear-gradient(90deg, transparent 0%, rgba(0,100,180,0.2) 30%, rgba(0,160,255,0.4) 50%, rgba(0,100,180,0.2) 70%, transparent 100%)",
          animationDelay: "2s",
        }}
      />

      {/* Subtle corner glass reflections */}
      <div
        className="absolute top-0 right-0 w-96 h-96 dark:hidden"
        style={{
          background: "radial-gradient(circle at 100% 0%, rgba(255,255,255,0.5) 0%, rgba(200,220,255,0.15) 30%, transparent 60%)",
          filter: "blur(30px)",
        }}
      />
      <div
        className="absolute top-0 right-0 w-96 h-96 hidden dark:block"
        style={{
          background: "radial-gradient(circle at 100% 0%, rgba(0,120,200,0.2) 0%, rgba(0,80,160,0.08) 30%, transparent 60%)",
          filter: "blur(30px)",
        }}
      />
      <div
        className="absolute bottom-0 left-0 w-80 h-80 dark:hidden"
        style={{
          background: "radial-gradient(circle at 0% 100%, rgba(220,235,255,0.3) 0%, rgba(200,210,255,0.1) 30%, transparent 60%)",
          filter: "blur(30px)",
        }}
      />
      <div
        className="absolute bottom-0 left-0 w-80 h-80 hidden dark:block"
        style={{
          background: "radial-gradient(circle at 0% 100%, rgba(0,100,180,0.15) 0%, rgba(0,60,140,0.06) 30%, transparent 60%)",
          filter: "blur(30px)",
        }}
      />

      {/* ECG wave layers - sharp neon cyan on white glass */}
      {layers.map((layer, i) => (
        <div
          key={i}
          className="ecg-scrolling"
          style={{
            position: "absolute",
            top: `${layer.top}%`,
            left: 0,
            width: "200%",
            height: "100px",
            animationDuration: `${layer.speed}s`,
          }}
        >
          <svg
            viewBox={`0 0 ${ECG_PERIOD * 2} 100`}
            preserveAspectRatio="none"
            className="w-full h-full"
          >
            <defs>
              <linearGradient id={`ecg-fade-light-${i}`} x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="#00a8e8" stopOpacity="0" />
                <stop offset="6%" stopColor="#00a8e8" stopOpacity={layer.opacity} />
                <stop offset="94%" stopColor="#00a8e8" stopOpacity={layer.opacity} />
                <stop offset="100%" stopColor="#00a8e8" stopOpacity="0" />
              </linearGradient>
              <linearGradient id={`ecg-fade-dark-${i}`} x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="#00d4ff" stopOpacity="0" />
                <stop offset="6%" stopColor="#00d4ff" stopOpacity={layer.opacity} />
                <stop offset="94%" stopColor="#00d4ff" stopOpacity={layer.opacity} />
                <stop offset="100%" stopColor="#00d4ff" stopOpacity="0" />
              </linearGradient>
              <filter id={`ecg-neon-light-${i}`}>
                <feGaussianBlur stdDeviation={layer.glowBlur} result="glow" />
                <feMerge>
                  <feMergeNode in="glow" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
              <filter id={`ecg-neon-dark-${i}`}>
                <feGaussianBlur stdDeviation={layer.glowBlur * 1.5} result="glow" />
                <feMerge>
                  <feMergeNode in="glow" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            {/* Neon glow layer - dark mode */}
            <path
              d={layer.path}
              fill="none"
              stroke="#00d4ff"
              strokeWidth={layer.stroke}
              strokeLinecap="square"
              strokeLinejoin="miter"
              vectorEffect="non-scaling-stroke"
              opacity={layer.glowOpacity}
              filter={`url(#ecg-neon-dark-${i})`}
              className="hidden dark:block"
            />
            <path
              d={layer.path}
              fill="none"
              stroke="#00d4ff"
              strokeWidth={layer.stroke}
              strokeLinecap="square"
              strokeLinejoin="miter"
              vectorEffect="non-scaling-stroke"
              opacity={layer.glowOpacity}
              filter={`url(#ecg-neon-dark-${i})`}
              transform={`translate(${ECG_PERIOD}, 0)`}
              className="hidden dark:block"
            />
            {/* Neon glow layer - light mode */}
            <path
              d={layer.path}
              fill="none"
              stroke="#00a8e8"
              strokeWidth={layer.stroke}
              strokeLinecap="square"
              strokeLinejoin="miter"
              vectorEffect="non-scaling-stroke"
              opacity={layer.glowOpacity * 0.7}
              filter={`url(#ecg-neon-light-${i})`}
              className="dark:hidden"
            />
            <path
              d={layer.path}
              fill="none"
              stroke="#00a8e8"
              strokeWidth={layer.stroke}
              strokeLinecap="square"
              strokeLinejoin="miter"
              vectorEffect="non-scaling-stroke"
              opacity={layer.glowOpacity * 0.7}
              filter={`url(#ecg-neon-light-${i})`}
              transform={`translate(${ECG_PERIOD}, 0)`}
              className="dark:hidden"
            />

            {/* Sharp core line - dark mode */}
            <path
              d={layer.path}
              fill="none"
              stroke={`url(#ecg-fade-dark-${i})`}
              strokeWidth={layer.stroke}
              strokeLinecap="square"
              strokeLinejoin="miter"
              vectorEffect="non-scaling-stroke"
              opacity={1}
              className="hidden dark:block"
            />
            <path
              d={layer.path}
              fill="none"
              stroke={`url(#ecg-fade-dark-${i})`}
              strokeWidth={layer.stroke}
              strokeLinecap="square"
              strokeLinejoin="miter"
              vectorEffect="non-scaling-stroke"
              opacity={1}
              transform={`translate(${ECG_PERIOD}, 0)`}
              className="hidden dark:block"
            />
            {/* Sharp core line - light mode */}
            <path
              d={layer.path}
              fill="none"
              stroke={`url(#ecg-fade-light-${i})`}
              strokeWidth={layer.stroke}
              strokeLinecap="square"
              strokeLinejoin="miter"
              vectorEffect="non-scaling-stroke"
              opacity={1}
              className="dark:hidden"
            />
            <path
              d={layer.path}
              fill="none"
              stroke={`url(#ecg-fade-light-${i})`}
              strokeWidth={layer.stroke}
              strokeLinecap="square"
              strokeLinejoin="miter"
              vectorEffect="non-scaling-stroke"
              opacity={1}
              transform={`translate(${ECG_PERIOD}, 0)`}
              className="dark:hidden"
            />
          </svg>
        </div>
      ))}
    </div>
  )
}