
import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
// @ts-ignore
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
// @ts-ignore
import { PLYLoader } from 'three/addons/loaders/PLYLoader.js';
import { Download, Maximize2, RotateCw, Loader2, AlertCircle, Box, Layers } from 'lucide-react';

interface PlyViewerProps {
  src: string;
}

export const PlyViewer: React.FC<PlyViewerProps> = ({ src }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  
  // Refs to keep track of Three.js objects for cleanup
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const frameIdRef = useRef<number>(0);
  const controlsRef = useRef<any>(null);

  useEffect(() => {
    if (!containerRef.current || !src) return;

    let isMounted = true;
    const container = containerRef.current;

    const init = async () => {
      try {
        setIsLoading(true);
        setError(null);

        // 1. Setup Scene
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0xffffff); // White background
        sceneRef.current = scene;

        // 2. Setup Camera
        const camera = new THREE.PerspectiveCamera(
          50, 
          container.clientWidth / container.clientHeight, 
          0.1, 
          100
        );
        camera.position.set(0, 0, 3); // Start back

        // 3. Setup Renderer
        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false }); // alpha false since we set background
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.setPixelRatio(window.devicePixelRatio);
        container.innerHTML = ''; // Clear previous
        container.appendChild(renderer.domElement);
        rendererRef.current = renderer;

        // 4. Setup Controls
        const controls = new OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        controls.autoRotate = true;
        controls.autoRotateSpeed = 2.0;
        controlsRef.current = controls;

        // 5. Load PLY
        const loader = new PLYLoader();
        loader.load(
          src,
          (geometry: THREE.BufferGeometry) => {
            if (!isMounted) return;

            // Center the geometry
            geometry.computeBoundingBox();
            if (geometry.boundingBox) {
              const center = new THREE.Vector3();
              geometry.boundingBox.getCenter(center);
              geometry.center(); // Re-centers geometry at 0,0,0
            }

            // Create Point Cloud
            // We use a small point size to simulate density
            const material = new THREE.PointsMaterial({ 
              size: 0.015, 
              vertexColors: true,
              sizeAttenuation: true 
            });
            const points = new THREE.Points(geometry, material);
            
            // Adjust rotation if needed (often PLY from python are inverted or rotated)
            points.rotation.x = -Math.PI; // Sometimes needed for Y-up correction
            
            scene.add(points);
            
            console.log("PLY Loaded successfully", geometry.attributes.position.count, "points");
            setIsLoading(false);
          },
          (xhr: ProgressEvent) => {
            // console.log((xhr.loaded / xhr.total * 100) + '% loaded');
          },
          (err: any) => {
            console.error("PLY Load Error", err);
            if (isMounted) {
              setError("Failed to parse PLY file.");
              setIsLoading(false);
            }
          }
        );

        // 6. Animation Loop
        const animate = () => {
          frameIdRef.current = requestAnimationFrame(animate);
          controls.update();
          renderer.render(scene, camera);
        };
        animate();

        // 7. Handle Resize
        const handleResize = () => {
          if (!container) return;
          const width = container.clientWidth;
          const height = container.clientHeight;
          camera.aspect = width / height;
          camera.updateProjectionMatrix();
          renderer.setSize(width, height);
        };
        window.addEventListener('resize', handleResize);
        
        // Return cleanup for resize listener
        return () => window.removeEventListener('resize', handleResize);

      } catch (e: any) {
        console.error("Three.js Init Error", e);
        if (isMounted) {
          setError(e.message || "Failed to initialize 3D viewer");
          setIsLoading(false);
        }
      }
    };

    const cleanupFn = init();

    return () => {
      isMounted = false;
      cancelAnimationFrame(frameIdRef.current);
      if (rendererRef.current) {
        rendererRef.current.dispose();
      }
      if (controlsRef.current) {
        controlsRef.current.dispose();
      }
      if (container) {
        container.innerHTML = '';
      }
      // Note: cleanupFn is a promise, we don't await it in cleanup
    };
  }, [src]);

  const toggleFullscreen = () => {
    if (!containerRef.current) return;
    
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen().catch(err => {
        console.error(`Error attempting to enable fullscreen: ${err.message}`);
      });
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  // Listen for fullscreen change events to update state
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  return (
    <div className="w-full h-full relative group">
      
      {/* 3D Canvas Container */}
      <div 
        ref={containerRef} 
        className="w-full h-full bg-white cursor-grab active:cursor-grabbing outline-none"
      />

      {/* Loading Overlay */}
      {isLoading && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-white z-20">
          <Loader2 className="w-10 h-10 text-indigo-600 animate-spin mb-4" />
          <p className="text-zinc-500 font-mono text-sm tracking-wider animate-pulse">LOADING POINTS...</p>
        </div>
      )}

      {/* Error Overlay with Fallback */}
      {error && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-white z-30 p-8 text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
          <h3 className="text-lg font-bold text-zinc-900 mb-2">Viewer Error</h3>
          <p className="text-zinc-600 text-sm mb-6 max-w-xs">{error}</p>
          <a 
            href={src}
            download="model.ply"
            className="px-4 py-2 bg-zinc-100 hover:bg-zinc-200 text-zinc-900 rounded-lg border border-zinc-200 transition-colors flex items-center gap-2"
          >
            <Download size={16} />
            Download PLY Instead
          </a>
        </div>
      )}

      {/* Controls Overlay (Visible on Hover or when loaded) */}
      {!isLoading && !error && (
        <>
          {/* Top Right Actions */}
          <div className="absolute top-4 right-4 flex flex-col gap-2 z-10">
            <button 
              onClick={toggleFullscreen}
              className="p-2 bg-black/80 hover:bg-black/90 backdrop-blur-md text-white rounded-lg border border-white/10 transition-colors shadow-lg"
              title="Toggle Fullscreen"
            >
              <Maximize2 size={20} />
            </button>
            <a 
              href={src}
              download="sculpture.ply"
              className="p-2 bg-indigo-600 hover:bg-indigo-700 backdrop-blur-md text-white rounded-lg border border-white/10 transition-colors shadow-lg"
              title="Download PLY File"
            >
              <Download size={20} />
            </a>
          </div>

          {/* Bottom Info / Instructions */}
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-300 w-max max-w-[90%]">
             <div className="bg-black/70 backdrop-blur-md px-4 py-2 rounded-full border border-white/10 flex items-center space-x-4 shadow-xl">
               <div className="flex items-center space-x-1.5">
                  <RotateCw size={12} className="text-indigo-400" />
                  <span className="text-[10px] text-zinc-200 font-medium uppercase tracking-wider">Rotate / Zoom</span>
               </div>
               <div className="w-px h-3 bg-white/20"></div>
               <div className="flex items-center space-x-1.5">
                  <Layers size={12} className="text-emerald-400" />
                  <span className="text-[10px] text-zinc-200 font-medium uppercase tracking-wider">Point Cloud Mode</span>
               </div>
             </div>
          </div>
        </>
      )}
    </div>
  );
};
