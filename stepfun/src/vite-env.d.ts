/// <reference types="vite/client" />

interface GPURequestAdapterOptions {
  powerPreference?: "low-power" | "high-performance";
}

interface GPUAdapter {}

interface GPU {
  requestAdapter(options?: GPURequestAdapterOptions): Promise<GPUAdapter | null>;
}

interface Navigator {
  gpu?: GPU;
}
