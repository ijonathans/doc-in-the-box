import { useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";

const PALETTE = ["#c084fc", "#60a5fa", "#ec4899"] as const;

function ParticleMesh() {
  const ref = useRef<THREE.Points>(null);
  const count = 2000;
  const radius = 1;

  const [positions, colors] = (() => {
    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);
    const colorVec = new THREE.Color();

    for (let i = 0; i < count; i++) {
      const phi = Math.acos(-1 + (2 * i) / count);
      const theta = Math.sqrt(count * Math.PI) * phi;
      positions[i * 3] = radius * Math.cos(theta) * Math.sin(phi);
      positions[i * 3 + 1] = radius * Math.sin(theta) * Math.sin(phi);
      positions[i * 3 + 2] = radius * Math.cos(phi);

      colorVec.set(PALETTE[i % PALETTE.length]);
      colors[i * 3] = colorVec.r;
      colors[i * 3 + 1] = colorVec.g;
      colors[i * 3 + 2] = colorVec.b;
    }
    return [positions, colors];
  })();

  useFrame((_state, delta) => {
    if (ref.current) {
      ref.current.rotation.y += delta * 0.2;
    }
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={count}
          array={positions}
          itemSize={3}
        />
        <bufferAttribute
          attach="attributes-color"
          count={count}
          array={colors}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.03}
        vertexColors
        transparent
        opacity={0.85}
        sizeAttenuation
        depthWrite={false}
      />
    </points>
  );
}

export function ParticleSphere() {
  return (
    <div className="relative h-28 w-28 shrink-0 overflow-hidden">
      <Canvas
        camera={{ position: [0, 0, 3], fov: 45 }}
        gl={{ antialias: true, alpha: true }}
        style={{ width: "100%", height: "100%" }}
      >
        <ParticleMesh />
      </Canvas>
    </div>
  );
}
