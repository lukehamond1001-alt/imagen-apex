
import React, { useState, useCallback, useEffect } from 'react';
import { PipelineSteps } from './components/PipelineSteps';
import { Button } from './components/Button';
import { ProgressBar } from './components/ProgressBar';
import { PlyViewer } from './components/PlyViewer';
import { generateImageFromText } from './services/geminiService';
import { generate3DFromImage, testEndpointConnection } from './services/vertexService';
import { PipelineStage, GeneratedImage } from './types';
import { Download, Sparkles, AlertTriangle, Box, Palette, Settings, Key, X, Eye, EyeOff, Globe, Activity, CheckCircle2, XCircle, ShieldAlert, Lock, WifiOff, Grip, MoreVertical } from 'lucide-react';
import { APP_NAME, VERTEX_ENDPOINT_URL, API_VERSION } from './constants';

const App: React.FC = () => {
  const [stage, setStage] = useState<PipelineStage>(PipelineStage.IDLE);
  const [prompt, setPrompt] = useState('');
  const [generatedImage, setGeneratedImage] = useState<GeneratedImage | null>(null);
  const [modelUrl, setModelUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDemoMode, setIsDemoMode] = useState(false);

  // Progress State
  const [progress, setProgress] = useState(0);

  // Settings State
  const [showSettings, setShowSettings] = useState(false);
  const [showToken, setShowToken] = useState(false);

  // Connection Testing State
  const [isTestingConnection, setIsTestingConnection] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'success' | 'error'>('idle');

  // Mixed Content State
  const [isMixedContent, setIsMixedContent] = useState(false);

  // Token State
  const [vertexToken, setVertexToken] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('vertexToken');
      if (saved !== null) return saved;
    }
    return "";
  });

  // Endpoint URL State
  const [endpointUrl, setEndpointUrl] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('endpointUrl');
      if (saved) return saved;
    }
    return VERTEX_ENDPOINT_URL;
  });

  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('vertexToken', vertexToken);
      localStorage.setItem('endpointUrl', endpointUrl);

      const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
      const isPageHttps = window.location.protocol === 'https:';
      const isEndpointHttp = endpointUrl.trim().toLowerCase().startsWith('http://');

      if (!isLocalhost && isPageHttps && isEndpointHttp) {
        setIsMixedContent(true);
      } else {
        setIsMixedContent(false);
      }
    }
  }, [vertexToken, endpointUrl]);

  // Simulated Progress Logic
  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;

    if (stage === PipelineStage.GENERATING_IMAGE) {
      setProgress(0);
      interval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 95) return 95;
          return prev + 5;
        });
      }, 150);
    } else if (stage === PipelineStage.CONVERTING_3D) {
      setProgress(0);
      interval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 90) return prev + 0.05;
          if (prev >= 95) return 95;
          return prev + 0.2;
        });
      }, 500);
    } else if (stage === PipelineStage.IMAGE_READY || stage === PipelineStage.COMPLETE) {
      setProgress(100);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [stage]);

  // API Key Selection State
  const [hasApiKey, setHasApiKey] = useState(false);

  useEffect(() => {
    const checkApiKey = async () => {
      if (window.aistudio) {
        const hasKey = await window.aistudio.hasSelectedApiKey();
        setHasApiKey(hasKey);
      } else {
        setHasApiKey(true);
      }
    };
    checkApiKey();
  }, []);

  const handleSelectApiKey = async () => {
    if (window.aistudio) {
      await window.aistudio.openSelectKey();
      setHasApiKey(true);
    }
  };

  const checkConnection = async () => {
    setIsTestingConnection(true);
    setConnectionStatus('idle');
    const isReachable = await testEndpointConnection(endpointUrl);
    setIsTestingConnection(false);
    setConnectionStatus(isReachable ? 'success' : 'error');
  };

  const handleGenerateImage = useCallback(async () => {
    if (!prompt.trim()) return;

    setStage(PipelineStage.GENERATING_IMAGE);
    setError(null);
    setGeneratedImage(null);
    setModelUrl(null);
    setIsDemoMode(false);

    try {
      const result = await generateImageFromText(prompt);
      setGeneratedImage(result);
      setStage(PipelineStage.IMAGE_READY);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to generate image';
      setError(errorMessage);
      setStage(PipelineStage.ERROR);

      if (errorMessage.includes("Requested entity was not found")) {
        setHasApiKey(false);
      }
    }
  }, [prompt]);

  const handleConvertTo3D = useCallback(async () => {
    if (!generatedImage) return;

    setStage(PipelineStage.CONVERTING_3D);
    setError(null);
    setIsDemoMode(false);

    try {
      const plyBlob = await generate3DFromImage(generatedImage.base64);
      if (!plyBlob) throw new Error("No PLY data received");
      const url = URL.createObjectURL(plyBlob);
      setModelUrl(url);
      setStage(PipelineStage.COMPLETE);
    } catch (err: any) {
      console.error("Critical 3D Conversion failure:", err);
      let errorMessage = err instanceof Error ? err.message : 'Failed to convert to 3D';

      if (isMixedContent && (errorMessage.includes("Failed to fetch") || errorMessage.includes("NetworkError"))) {
        errorMessage = `Browser blocked the request. Please see the yellow "Connection Blocked" banner at the top of the page.`;
      }

      setError(errorMessage);
      setStage(PipelineStage.ERROR);
    }
  }, [generatedImage, isMixedContent]);

  const handleReset = () => {
    setStage(PipelineStage.IDLE);
    setPrompt('');
    setGeneratedImage(null);
    setModelUrl(null);
    setError(null);
    setIsDemoMode(false);
    setProgress(0);
  };

  const download2DImage = () => {
    if (!generatedImage) return;
    const link = document.createElement('a');
    link.href = `data:${generatedImage.mimeType};base64,${generatedImage.base64}`;
    link.download = `concept-${Date.now()}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // --- RENDERING ---

  if (!hasApiKey) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center p-4 font-sans text-zinc-100">
        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-8 max-w-md w-full text-center shadow-2xl">
          <div className="w-16 h-16 bg-indigo-500/20 rounded-2xl flex items-center justify-center mx-auto mb-6">
            <Key className="w-8 h-8 text-indigo-400" />
          </div>
          <h2 className="text-xl font-bold text-white mb-2">API Key Required</h2>
          <p className="text-zinc-400 mb-6">
            To generate AI images and 3D models, please select a valid API key from your GCP project.
          </p>
          <Button onClick={handleSelectApiKey} className="w-full mb-4">
            Select API Key
          </Button>
          <a
            href="https://ai.google.dev/gemini-api/docs/billing"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-zinc-500 hover:text-indigo-400 transition-colors"
          >
            Billing Documentation
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-zinc-950 text-zinc-100 font-sans overflow-hidden">

      {/* ==================== LEFT SIDEBAR ==================== */}
      <aside className="w-full md:w-[400px] flex flex-col border-r border-zinc-800 bg-zinc-900 z-10 shadow-2xl">

        {/* Header Logo */}
        <div className="h-16 flex items-center justify-between px-6 border-b border-zinc-800 shrink-0">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 relative group">
              <div className="absolute inset-0 bg-indigo-500 blur opacity-40"></div>
              <div className="relative w-full h-full bg-zinc-800 border border-white/10 rounded-lg flex items-center justify-center">
                <Box size={16} className="text-white" />
              </div>
            </div>
            <span className="font-bold text-lg tracking-tight text-zinc-100">
              {APP_NAME}
            </span>
          </div>
          <button onClick={() => setShowSettings(true)} className="p-2 text-zinc-500 hover:text-zinc-300 transition-colors">
            <Settings size={18} />
          </button>
        </div>

        {/* Scrollable Content Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-8 custom-scrollbar">

          {/* Status Tracker */}
          <section>
            <PipelineSteps stage={stage} />
          </section>

          {/* Prompt Input */}
          <section className="space-y-3">
            <div className="flex justify-between items-baseline">
              <label className="text-xs font-mono text-zinc-400 uppercase tracking-wider">Prompt</label>
              {stage !== PipelineStage.IDLE && (
                <button onClick={handleReset} className="text-xs text-indigo-400 hover:text-indigo-300">
                  Reset
                </button>
              )}
            </div>
            <div className="relative">
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="A futuristic cybernetic helmet with neon accents..."
                className="w-full bg-zinc-950 border border-zinc-800 rounded-xl p-4 text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all resize-none h-32"
                disabled={stage !== PipelineStage.IDLE && stage !== PipelineStage.IMAGE_READY && stage !== PipelineStage.COMPLETE && stage !== PipelineStage.ERROR}
              />
              <div className="absolute bottom-3 right-3">
                <Sparkles size={14} className={prompt ? "text-indigo-500" : "text-zinc-700"} />
              </div>
            </div>

            {/* Main Action Button */}
            {stage === PipelineStage.IDLE || stage === PipelineStage.GENERATING_IMAGE || stage === PipelineStage.ERROR ? (
              <Button
                onClick={handleGenerateImage}
                disabled={!prompt.trim() || stage === PipelineStage.GENERATING_IMAGE}
                isLoading={stage === PipelineStage.GENERATING_IMAGE}
                className="w-full"
              >
                Generate Concept
              </Button>
            ) : null}
          </section>

          {/* 2D Preview / Transformation Section */}
          <section className="space-y-3">
            <label className="text-xs font-mono text-zinc-400 uppercase tracking-wider">Concept Preview</label>

            <div className={`relative aspect-square rounded-xl overflow-hidden border bg-zinc-950 group transition-all duration-500 ${generatedImage ? 'border-indigo-500/30 shadow-lg' : 'border-zinc-800 border-dashed'
              }`}>

              {generatedImage ? (
                <>
                  <img
                    src={`data:${generatedImage.mimeType};base64,${generatedImage.base64}`}
                    alt="Concept"
                    className="w-full h-full object-cover"
                  />

                  {/* Overlay for Image Ready */}
                  <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                    <button onClick={download2DImage} className="p-2 bg-white/10 hover:bg-white/20 backdrop-blur rounded-lg text-white transition-colors" title="Download Image">
                      <Download size={18} />
                    </button>
                  </div>

                  {/* Loading Bar for 3D Gen */}
                  {stage === PipelineStage.CONVERTING_3D && (
                    <div className="absolute inset-x-4 bottom-4 bg-zinc-900/90 backdrop-blur rounded-lg p-3 border border-white/10 shadow-xl">
                      <ProgressBar progress={progress} label="Sculpting..." />
                    </div>
                  )}

                  {/* Transformation Trigger */}
                  {stage === PipelineStage.IMAGE_READY && (
                    <div className="absolute inset-x-4 bottom-4">
                      <Button onClick={handleConvertTo3D} className="w-full shadow-xl">
                        <Box className="w-4 h-4 mr-2" />
                        Sculpt 3D Model
                      </Button>
                    </div>
                  )}
                </>
              ) : (
                <div className="absolute inset-0 flex flex-col items-center justify-center text-zinc-700">
                  <Palette size={24} className="mb-2 opacity-50" />
                  <span className="text-xs">No concept generated</span>
                </div>
              )}
            </div>
          </section>

          {/* Errors */}
          {error && (
            <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 flex items-start space-x-3 text-red-200">
              <AlertTriangle size={16} className="shrink-0 text-red-400 mt-0.5" />
              <span className="text-xs">{error}</span>
            </div>
          )}

          {/* Mixed Content Warning */}
          {isMixedContent && (
            <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
              <div className="flex items-center space-x-2 text-amber-300 mb-1">
                <ShieldAlert size={14} />
                <span className="text-xs font-bold uppercase">Connection Blocked</span>
              </div>
              <p className="text-[10px] text-amber-200/70 leading-relaxed">
                The browser blocked the 3D server connection. Please allow <strong>Insecure Content</strong> in site settings.
              </p>
            </div>
          )}
        </div>

        {/* Footer Info */}
        <div className="p-4 border-t border-zinc-800 bg-zinc-900 text-[10px] text-zinc-600 flex justify-between">
          <span>{API_VERSION}</span>
          <span>Google Gemini + Vertex AI</span>
        </div>
      </aside>

      {/* ==================== MAIN VIEWPORT ==================== */}
      <main className="flex-1 relative bg-zinc-950 flex flex-col">

        {modelUrl ? (
          <PlyViewer src={modelUrl} />
        ) : (
          /* Empty State Hero */
          <div className="flex-1 flex flex-col items-center justify-center text-zinc-800 p-8 relative overflow-hidden">
            {/* Grid Background Pattern */}
            <div className="absolute inset-0 opacity-10"
              style={{ backgroundImage: 'radial-gradient(circle at 1px 1px, #71717a 1px, transparent 0)', backgroundSize: '40px 40px' }}>
            </div>

            <div className="relative z-10 text-center max-w-lg">
              <div className="w-32 h-32 mx-auto bg-zinc-900 rounded-full border border-zinc-800 flex items-center justify-center mb-8 shadow-2xl relative">
                <div className="absolute inset-0 rounded-full border border-indigo-500/20 animate-pulse"></div>
                <Box size={48} className="text-zinc-700" />
              </div>
              <h1 className="text-3xl font-bold text-zinc-700 mb-4">Ready to Sculpt</h1>
              <p className="text-zinc-600 text-lg">
                Enter a prompt in the sidebar to generate a 2D concept, then transform it into a 3D point cloud model.
              </p>
            </div>
          </div>
        )}

      </main>

      {/* ==================== SETTINGS MODAL ==================== */}
      {showSettings && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl w-full max-w-2xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="px-6 py-4 border-b border-zinc-800 flex justify-between items-center bg-zinc-900/50">
              <h3 className="text-lg font-semibold text-zinc-100 flex items-center gap-2">
                <Settings size={18} /> Configuration
              </h3>
              <button onClick={() => setShowSettings(false)} className="text-zinc-500 hover:text-white transition-colors">
                <X size={20} />
              </button>
            </div>

            <div className="p-6 space-y-6">

              {/* Endpoint Setting */}
              <div>
                <label className="block text-xs font-mono text-zinc-500 mb-2 flex items-center uppercase tracking-wider">
                  <Globe size={14} className="mr-2" /> Backend Endpoint URL
                </label>
                <div className="flex gap-3">
                  <input
                    type="text"
                    value={endpointUrl}
                    onChange={(e) => {
                      setEndpointUrl(e.target.value);
                      setConnectionStatus('idle');
                    }}
                    className="flex-1 bg-zinc-950 border border-zinc-700 rounded-lg py-2.5 px-4 text-sm text-zinc-200 focus:ring-2 focus:ring-indigo-500 outline-none font-mono"
                  />
                  <button
                    onClick={checkConnection}
                    disabled={isTestingConnection}
                    className={`px-4 rounded-lg border font-medium text-sm flex items-center gap-2 transition-colors ${connectionStatus === 'success' ? 'bg-green-500/10 border-green-500/50 text-green-400' :
                        connectionStatus === 'error' ? 'bg-red-500/10 border-red-500/50 text-red-400' :
                          'bg-zinc-800 border-zinc-700 text-zinc-400 hover:bg-zinc-700'
                      }`}
                  >
                    {isTestingConnection ? <Activity size={16} className="animate-spin" /> :
                      connectionStatus === 'success' ? <><CheckCircle2 size={16} /> Connected</> :
                        connectionStatus === 'error' ? <><XCircle size={16} /> Failed</> :
                          "Test"}
                  </button>
                </div>
                <p className="text-[11px] text-zinc-600 mt-2">
                  Direct URL to the L4 GPU Cluster (SAM 3D). Ensure Mixed Content is allowed if URL is HTTP.
                </p>
              </div>

              {/* API Key Setting */}
              <div>
                <label className="block text-xs font-mono text-zinc-500 mb-2 flex items-center uppercase tracking-wider">
                  <Key size={14} className="mr-2" /> Backend Auth Token
                </label>
                <div className="relative">
                  <input
                    type={showToken ? "text" : "password"}
                    value={vertexToken}
                    onChange={(e) => setVertexToken(e.target.value)}
                    className="w-full bg-zinc-950 border border-zinc-700 rounded-lg py-2.5 px-4 pr-10 text-sm text-zinc-200 focus:ring-2 focus:ring-indigo-500 outline-none font-mono"
                  />
                  <button
                    onClick={() => setShowToken(!showToken)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300"
                  >
                    {showToken ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

            </div>

            <div className="px-6 py-4 bg-zinc-950/50 border-t border-zinc-800 flex justify-end">
              <Button variant="secondary" onClick={() => setShowSettings(false)}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};

export default App;
