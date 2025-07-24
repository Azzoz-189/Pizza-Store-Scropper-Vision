import { useEffect, useState, useRef, useCallback } from 'react';
import './App.css';

// Icons
import { FiUpload, FiPlay, FiPause, FiVolume2, FiVolumeX, FiMaximize, FiMinimize } from 'react-icons/fi';
import { FaExclamationTriangle } from 'react-icons/fa';

const WS_URL = 'ws://localhost:8004/ws';
const UPLOAD_URL = 'http://localhost:8000/upload';

// Sample videos from the directory
const sampleVideos = [
  {
    id: 1,
    name: 'Kitchen Inspection 1',
    filename: 'Sah w b3dha ghalt.mp4',
    duration: '1:45',
    date: '2023-07-20',
    thumbnail: 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMjAiIGhlaWdodD0iNjgiIHZpZXdCb3g9IjAgMCAxMjAgNjgiPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9IiNlZWVlZWUiLz48dGV4dCB4PSI1MCUiIHk9IjUwJSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE0IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBhbGlnbm1lbnQtYmFzZWxpbmU9Im1pZGRsZSIgZmlsbD0iIzY2NiI+S2l0Y2hlbiAxPC90ZXh0Pjwvc3ZnPg==',
  },
  {
    id: 2,
    name: 'Kitchen Inspection 2',
    filename: 'Sah w b3dha ghalt (2).mp4',
    duration: '2:15',
    date: '2023-07-21',
    thumbnail: 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMjAiIGhlaWdodD0iNjgiIHZpZXdCb3g9IjAgMCAxMjAgNjgiPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9IiNlZWVlZWUiLz48dGV4dCB4PSI1MCUiIHk9IjUwJSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE0IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBhbGlnbm1lbnQtYmFzZWxpbmU9Im1pZGRsZSIgZmlsbD0iIzY2NiI+S2l0Y2hlbiAyPC90ZXh0Pjwvc3ZnPg==',
  },
  {
    id: 3,
    name: 'Kitchen Inspection 3',
    filename: 'Sah w b3dha ghalt (3).mp4',
    duration: '1:30',
    date: '2023-07-22',
    thumbnail: 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMjAiIGhlaWdodD0iNjgiIHZpZXdCb3g9IjAgMCAxMjAgNjgiPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9IiNlZWVlZWUiLz48dGV4dCB4PSI1MCUiIHk9IjUwJSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE0IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBhbGlnbm1lbnQtYmFzZWxpbmU9Im1pZGRsZSIgZmlsbD0iIzY2NiI+S2l0Y2hlbiAzPC90ZXh0Pjwvc3ZnPg==',
  },
];

const sampleViolations = [
  { id: 1, type: 'No Hairnet', time: '00:02:34', confidence: 92, severity: 'high' },
  { id: 2, type: 'Bare Hands', time: '00:05:12', confidence: 88, severity: 'medium' },
  { id: 3, type: 'No Gloves', time: '00:07:45', confidence: 95, severity: 'high' },
];

function App() {
  // Video player state
  const [videoSource, setVideoSource] = useState('');
  const [selectedVideo, setSelectedVideo] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState('idle'); // 'idle', 'uploading', 'processing', 'completed', 'error'
  const [status, setStatus] = useState('Ready to analyze video');
  const [violations, setViolations] = useState([]);
  const [showViolationDetails, setShowViolationDetails] = useState(null);
  const [activeTab, setActiveTab] = useState('videos');
  const [isProcessing, setIsProcessing] = useState(false);
  const [connected, setConnected] = useState(false);
  const [connectionError, setConnectionError] = useState(null);
  const [currentFrame, setCurrentFrame] = useState({});
  const [trackedObjects, setTrackedObjects] = useState({});
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.5);
  const [lastConfidenceUpdate, setLastConfidenceUpdate] = useState(Date.now());
  const canvasRef = useRef(null);
  const wsRef = useRef(null);
  const sidebarRef = useRef(null);
  const fileInputRef = useRef(null);

  // Toggle play/pause
  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  // Handle video time update
  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  };

  // Format time (seconds to MM:SS)
  const formatTime = (time) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
  };

  // Handle video selection and start analysis
  const handleVideoSelect = useCallback(async (video) => {
    try {
      // Clear any existing timeouts/intervals to prevent memory leaks
      const existingInterval = window.videoAnalysisInterval;
      if (existingInterval) {
        clearInterval(existingInterval);
      }
      
      // Update UI state first
      setSelectedVideo(video);
      setUploadStatus('processing');
      setStatus('Preparing video analysis...');
      setViolations([]);
      setCurrentFrame({});
      setTrackedObjects({});

      // Set the video source
      setVideoSource(`/videos/${video.filename}`);
      
      // Small delay to ensure video element is ready
      await new Promise(resolve => setTimeout(resolve, 100));

      const sendStartAnalysis = () => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          const message = {
            type: 'start_analysis',
            video_id: video.id,
            filename: video.filename,
            confidence_threshold: confidenceThreshold
          };
          console.log('Sending start_analysis with confidence:', confidenceThreshold);
          wsRef.current.send(JSON.stringify(message));
          return true;
        }
        return false;
      };

      // Try to send immediately if connected
      if (!sendStartAnalysis()) {
        setStatus('Connecting to analysis server...');
        
        // Set up a connection check with cleanup
        let retryCount = 0;
        const maxRetries = 30; // 30 * 200ms = 6 seconds max
        
        const checkConnection = () => {
          if (sendStartAnalysis()) {
            clearInterval(intervalId);
            return;
          }
          
          retryCount++;
          if (retryCount >= maxRetries) {
            clearInterval(intervalId);
            setStatus('Failed to connect to analysis server');
            setUploadStatus('error');
          }
        };
        
        const intervalId = setInterval(checkConnection, 200);
        window.videoAnalysisInterval = intervalId;
        
        // Initial check
        checkConnection();
      }
    } catch (error) {
      console.error('Error starting analysis:', error);
      setStatus('Error starting analysis');
      setUploadStatus('error');
    }
  }, [confidenceThreshold]); // Add dependencies here

  // WebSocket connection management
  useEffect(() => {
    let isMounted = true;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;
    let reconnectTimeout = null;
    let connectionCheckInterval = null;

    const connectWebSocket = () => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        console.log('WebSocket already connected');
        return;
      }

      // Close existing connection if any
      if (wsRef.current) {
        wsRef.current.close();
      }

      console.log(`Connecting to WebSocket at ${WS_URL}...`);
      setStatus('Connecting to analysis server...');
      setConnectionError(null);

      try {
        wsRef.current = new WebSocket(WS_URL);

        wsRef.current.onopen = () => {
          console.log('WebSocket connected successfully');
          reconnectAttempts = 0;
          
          // Clear any pending reconnection attempts
          if (reconnectTimeout) {
            clearTimeout(reconnectTimeout);
            reconnectTimeout = null;
          }
          
          if (!isMounted) return;
          
          setConnected(true);
          setStatus('Connected to analysis server');
          setConnectionError(null);

          // If we have a selected video, send its ID to start analysis
          if (selectedVideo) {
            // Small delay to ensure everything is ready
            setTimeout(() => {
              if (wsRef.current?.readyState === WebSocket.OPEN && isMounted) {
                console.log('Sending start_analysis message for video:', selectedVideo.filename);
                const message = {
                  type: 'start_analysis',
                  video_id: selectedVideo.id,
                  filename: selectedVideo.filename,
                  confidence_threshold: confidenceThreshold
                };
                console.log('Sending message:', message);
                wsRef.current.send(JSON.stringify(message));
              }
            }, 100);
          }
          
          // Set up periodic connection check
          if (connectionCheckInterval) {
            clearInterval(connectionCheckInterval);
          }
          
          connectionCheckInterval = setInterval(() => {
            if (wsRef.current?.readyState !== WebSocket.OPEN) {
              console.log('WebSocket connection lost, reconnecting...');
              clearInterval(connectionCheckInterval);
              connectWebSocket();
            }
          }, 10000); // Check every 10 seconds
        };

        wsRef.current.onerror = (error) => {
          console.error('WebSocket error:', error);
          if (isMounted) {
            setConnectionError(`WebSocket error: ${error.message || 'Unknown error'}`);
            
            // Try to reconnect if not already reconnecting
            if (!reconnectTimeout) {
              const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
              console.log(`Scheduling reconnection attempt in ${delay}ms...`);
              
              reconnectTimeout = setTimeout(() => {
                reconnectAttempts++;
                console.log(`Reconnect attempt ${reconnectAttempts}/${maxReconnectAttempts}`);
                connectWebSocket();
              }, delay);
            }
          }
        };

        wsRef.current.onclose = (event) => {
          console.log('WebSocket connection closed', event);
          if (isMounted) {
            setConnected(false);
            setStatus('Disconnected from analysis server');

            // Attempt to reconnect if this wasn't a clean close
            if (event.code !== 1000 && reconnectAttempts < maxReconnectAttempts) {
              const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
              console.log(`Attempting to reconnect in ${delay}ms...`);

              reconnectTimeout = setTimeout(() => {
                reconnectAttempts++;
                console.log(`Reconnect attempt ${reconnectAttempts}/${maxReconnectAttempts}`);
                connectWebSocket();
              }, delay);
            } else if (event.code !== 1000) {
              setConnectionError('Failed to reconnect. Please refresh the page to try again.');
            }
          }
        };

        wsRef.current.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log('Received WebSocket message:', data);

            // Handle different message types
            switch (data.type) {
              case 'status':
                setStatus(data.message);
                // Update progress if available
                if (typeof data.progress === 'number') {
                  setUploadProgress(Math.round(data.progress));

                  // If progress is complete, update status
                  if (data.progress >= 100) {
                    setUploadStatus('completed');
                    setStatus('Analysis complete' + (data.violations_found ? ` - Found ${data.violations_found} violations` : ''));

                    // Auto-hide status after delay
                    setTimeout(() => setUploadStatus('idle'), 5000);
                  } else if (data.progress > 0) {
                    setUploadStatus('processing');
                  }
                }
                break;

              case 'frame':
                // Update current frame data for visualization
                setCurrentFrame(prev => ({
                  ...prev,
                  ...data,
                  timestamp: data.timestamp || new Date().toISOString()
                }));

                // Update processing status based on frame data
                if (data.progress !== undefined) {
                  const progress = Math.round(data.progress);
                  setUploadProgress(progress);

                  if (progress >= 100) {
                    setUploadStatus('completed');
                    setStatus('Analysis complete' + (data.violations_found ? ` - Found ${data.violations_found} violations` : ''));

                    // Auto-hide status after delay
                    setTimeout(() => setUploadStatus('idle'), 5000);
                  } else if (progress > 0) {
                    setUploadStatus('processing');
                    setStatus(`Processing: ${progress}% complete`);
                  }
                }

                // Extract and process detections
                if (data.detections?.length > 0) {
                  // Filter detections by confidence threshold
                  const validDetections = data.detections.filter(d => d.confidence >= confidenceThreshold);

                  // Update tracked objects
                  const trackedObjs = validDetections.filter(d => d.track_id);
                  if (trackedObjs.length > 0) {
                    setTrackedObjects(prev => ({
                      ...prev,
                      ...Object.fromEntries(trackedObjs.map(obj => [obj.track_id, obj]))
                    }));
                  }

                  // Extract and add violations
                  const violations = validDetections.filter(d => d.type === 'violation');
                  if (violations.length > 0) {
                    const newViolations = violations.map(violation => ({
                      ...violation,
                      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
                      timestamp: violation.timestamp || new Date().toISOString(),
                      // Ensure required fields have default values
                      type: violation.type || 'violation',
                      confidence: violation.confidence || 0,
                      severity: violation.severity || 'medium',
                      bbox: violation.bbox || [0, 0, 0, 0],
                      label: violation.label || 'Violation',
                      description: violation.description || 'A potential violation was detected'
                    }));

                    setViolations(prev => [...newViolations, ...prev].slice(0, 100));

                    // Show notification for new violations
                    newViolations.forEach(violation => {
                      console.log(`New violation: ${violation.label} (${(violation.confidence * 100).toFixed(1)}%)`);
                    });
                  }
                }
                break;

              case 'error':
                console.error('Server error:', data.message);
                setStatus(`Error: ${data.message}`);
                setUploadStatus('error');
                break;

              default:
                console.log('Unhandled message type:', data.type);
            }
          } catch (err) {
            console.error('Error processing WebSocket message:', err);
          }
        };
      } catch (error) {
        console.error('Error setting up WebSocket:', error);
        if (isMounted) {
          setStatus('Error setting up connection');
          setConnectionError(error.message);
        }
      }
    };

    // Initial connection
    connectWebSocket();

    // Cleanup function
    return () => {
      isMounted = false;

      // Clear any pending reconnection attempts
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
        reconnectTimeout = null;
      }
      
      // Clear connection check interval
      if (connectionCheckInterval) {
        clearInterval(connectionCheckInterval);
        connectionCheckInterval = null;
      }

      // Clear any video analysis interval
      if (window.videoAnalysisInterval) {
        clearInterval(window.videoAnalysisInterval);
        window.videoAnalysisInterval = null;
      }

      // Close WebSocket connection if it exists
      if (wsRef.current) {
        // Only close if not already closed or closing
        if (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING) {
          // Remove all event listeners
          wsRef.current.onopen = null;
          wsRef.current.onclose = null;
          wsRef.current.onerror = null;
          wsRef.current.onmessage = null;
          
          // Close the connection
          wsRef.current.close();
          wsRef.current = null;
        }
      }
    };
  }, [selectedVideo]); // Re-run effect if selectedVideo changes

  // Handle file upload
  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Reset any previous state
    setUploadProgress(0);
    setIsProcessing(true);

    const formData = new FormData();
    formData.append('video', file);

    try {
      console.log('Starting file upload...');

      // Create a new XMLHttpRequest for better progress tracking
      const xhr = new XMLHttpRequest();

      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const progress = Math.round((event.loaded / event.total) * 100);
          console.log(`Upload progress: ${progress}%`);
          setUploadProgress(progress);
        }
      };

      // Set up the request
      xhr.open('POST', UPLOAD_URL, true);

      // Handle response
      xhr.onload = () => {
        setUploadStatus('processing');
        setStatus('Processing video...');
        console.log('Upload response:', xhr.status, xhr.statusText);

        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const data = JSON.parse(xhr.responseText);
            console.log('Upload successful:', data);
            const videoUrl = URL.createObjectURL(file);
            console.log('Created video URL:', videoUrl);
            setVideoSource(videoUrl);
            setStatus('Video uploaded. Processing...');

            // Update confidence threshold and notify server
            const updateConfidenceThreshold = useCallback((newThreshold) => {
              setConfidenceThreshold(newThreshold);
              setLastConfidenceUpdate(Date.now());

              // Only send update if we're connected and have a selected video
              // Throttle updates to avoid overwhelming the server
              if (wsRef.current?.readyState === WebSocket.OPEN && selectedVideo) {
                clearTimeout(confidenceUpdateTimeout.current);
                confidenceUpdateTimeout.current = setTimeout(() => {
                  const message = {
                    type: 'update_confidence',
                    confidence_threshold: newThreshold,
                    video_id: selectedVideo.id
                  };
                  console.log('Updating confidence threshold:', newThreshold);
                  wsRef.current.send(JSON.stringify(message));
                }, 300); // 300ms debounce
              }
            }, [selectedVideo]);

            // Store the timeout ID for confidence updates
            const confidenceUpdateTimeout = useRef(null);

            // Notify backend
            if (wsRef.current?.readyState === WebSocket.OPEN) {
              wsRef.current.send(JSON.stringify({
                type: 'process_video',
                video_id: data.video_id,
                file_name: file.name
              }));
            }
          } catch (parseError) {
            console.error('Error parsing response:', parseError);
            throw new Error('Invalid response from server');
          }
        } else {
          console.error('Upload failed with status:', xhr.status, xhr.statusText);
          console.error('Response text:', xhr.responseText);
          throw new Error(`Upload failed: ${xhr.status} ${xhr.statusText}`);
        }
      };
      
      // Handle network errors
      xhr.onerror = () => {
        console.error('Network error during upload');
        throw new Error('Network error. Please check your connection.');
      };
      
      // Send the request
      xhr.send(formData);
      
    } catch (error) {
      console.error('Error during file upload:', error);
      alert(`Upload failed: ${error.message || 'Unknown error'}`);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className={`app ${isFullscreen ? 'fullscreen' : ''}`}>
      {/* Header */}
      <header className="app-header">
        <div className="logo">
          <FaExclamationTriangle className="logo-icon" />
          <h1>HygieneGuard AI</h1>
        </div>
        <div className="header-controls">
          <div className={`connection-status ${connected ? 'connected' : 'disconnected'}`}>
            <div className="status-indicator"></div>
            <span className="status-text">{connected ? 'Connected' : 'Disconnected'}</span>
            <span className="status-message">{status}</span>
          </div>
          <button className="btn btn-primary" onClick={() => fileInputRef.current?.click()}>
            <FiUpload className="btn-icon" /> Upload Video
          </button>
          <input
            type="file"
            ref={fileInputRef}
            accept="video/*"
            onChange={handleFileUpload}
            style={{ display: 'none' }}
          />
        </div>
      </header>

      {/* Upload Progress Bar */}
      {(uploadStatus === 'uploading' || uploadStatus === 'processing') && (
        <div className="upload-progress-container">
          <div className="upload-progress">
            <div 
              className={`progress-bar ${uploadStatus}`} 
              style={{ width: `${uploadStatus === 'processing' ? 100 : uploadProgress}%` }}
            ></div>
            <div className="progress-text">
              {uploadStatus === 'uploading' ? (
                <span>Uploading: {uploadProgress}%</span>
              ) : (
                <span>Processing video... <span className="processing-dots">•••</span></span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="main-content">
        {/* Left Sidebar */}
        <aside className="sidebar" ref={sidebarRef}>
          <div className="sidebar-tabs">
            <button 
              className={`tab-btn ${activeTab === 'videos' ? 'active' : ''}`}
              onClick={() => setActiveTab('videos')}
            >
              Videos
            </button>
            <button 
              className={`tab-btn ${activeTab === 'violations' ? 'active' : ''}`}
              onClick={() => setActiveTab('violations')}
            >
              Violations
            </button>
          </div>

          <div className="tab-content">
            {activeTab === 'videos' ? (
              <div className="video-list">
                <h3>Recent Videos</h3>
                {sampleVideos.map((video) => (
                  <div 
                    key={video.id} 
                    className={`video-item ${selectedVideo?.id === video.id ? 'active' : ''}`}
                  >
                    <div className="video-thumbnail">
                      <img src={video.thumbnail} alt={video.name} />
                      <span className="video-duration">{video.duration}</span>
                      <div className="video-overlay">
                        <button 
                          className="analyze-btn"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleVideoSelect(video);
                          }}
                        >
                          Analyze
                        </button>
                      </div>
                    </div>
                    <div className="video-info">
                      <h4>{video.name}</h4>
                      <div className="video-meta">
                        <span>{video.date}</span>
                        <span>{video.duration}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="violations-list">
                <h3>Detected Violations</h3>
                {violations.length > 0 ? (
                  violations.map((violation) => (
                    <div 
                      key={violation.id} 
                      className={`violation-item ${violation.severity}`}
                      onClick={() => setShowViolationDetails(violation)}
                    >
                      <div className="violation-icon">
                        <FaExclamationTriangle />
                      </div>
                      <div className="violation-details">
                        <div className="violation-type">{violation.type}</div>
                        <div className="violation-time">{violation.time}</div>
                      </div>
                      <div className="violation-confidence">
                        {violation.confidence}%
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="no-violations">
                    <p>No violations detected</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </aside>

        {/* Main Video Area */}
        <main className="video-container">
          <div className="video-wrapper">
            {videoSource ? (
              <>
                <video
                  ref={videoRef}
                  src={videoSource}
                  className="video-player"
                  onClick={togglePlay}
                  onTimeUpdate={handleTimeUpdate}
                  onLoadedMetadata={() => setDuration(videoRef.current?.duration || 0)}
                  onEnded={() => setIsPlaying(false)}
                  muted={isMuted}
                />
                <canvas ref={canvasRef} className="video-canvas" />
                
                {/* Video Controls */}
                <div className="video-controls">
                  <button className="control-btn" onClick={togglePlay}>
                    {isPlaying ? <FiPause /> : <FiPlay />}
                  </button>
                  
                  <div className="time-display">
                    {formatTime(currentTime)} / {formatTime(duration)}
                  </div>
                  
                  <input
                    type="range"
                    min="0"
                    max={duration || 100}
                    value={currentTime}
                    onChange={(e) => {
                      if (videoRef.current) {
                        videoRef.current.currentTime = e.target.value;
                        setCurrentTime(parseFloat(e.target.value));
                      }
                    }}
                    className="progress-bar"
                  />
                  
                  <div className="volume-control">
                    <button className="control-btn" onClick={() => setIsMuted(!isMuted)}>
                      {isMuted ? <FiVolumeX /> : <FiVolume2 />}
                    </button>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.01"
                      value={volume}
                      onChange={(e) => {
                        const newVolume = parseFloat(e.target.value);
                        setVolume(newVolume);
                        if (videoRef.current) {
                          videoRef.current.volume = newVolume;
                          setIsMuted(newVolume === 0);
                        }
                      }}
                      className="volume-slider"
                    />
                  </div>
                  
                  <button 
                    className="control-btn fullscreen-btn"
                    onClick={() => setIsFullscreen(!isFullscreen)}
                  >
                    {isFullscreen ? <FiMinimize /> : <FiMaximize />}
                  </button>
                </div>
                
                {/* Video Info */}
                <div className="video-info">
                  <h2>{selectedVideo?.name || 'No video selected'}</h2>
                  <div className="confidence-control">
                    <label>Detection Confidence: <strong>{Math.round(confidenceThreshold * 100)}%</strong></label>
                    <input
                      type="range"
                      min="0.1"
                      max="0.95"
                      step="0.05"
                      value={confidenceThreshold}
                      onChange={(e) => updateConfidenceThreshold(parseFloat(e.target.value))}
                      className="confidence-slider"
                      title={`Adjust detection sensitivity: ${Math.round(confidenceThreshold * 100)}%`}
                    />
                  </div>
                </div>
              </>
            ) : (
              <div className="no-video-selected">
                <FiUpload size={48} />
                <h3>No Video Selected</h3>
                <p>Upload a video or select one from the sidebar to begin analysis</p>
                <button 
                  className="btn btn-primary" 
                  onClick={() => fileInputRef.current?.click()}
                >
                  <FiUpload className="btn-icon" /> Upload Video
                </button>
              </div>
            )}
          </div>
          
          {/* Detection Stats */}
          {videoSource && (
            <div className="detection-stats">
              <div className="stat-card">
                <h4>Violations</h4>
                <div className="stat-value">{violations.length}</div>
              </div>
              <div className="stat-card">
                <h4>Detection Confidence</h4>
                <div className="stat-value">{Math.round(confidenceThreshold * 100)}%</div>
              </div>
              <div className="stat-card">
                <h4>Current Time</h4>
                <div className="stat-value">{formatTime(currentTime)}</div>
              </div>
            </div>
          )}
        </main>
      </div>
      
      {/* Status Bar */}
      <div className="status-bar">
        <div className="status-message">
          {isProcessing ? (
            <div className="upload-progress">
              <div className="progress-bar" style={{ width: `${uploadProgress}%` }}></div>
              <span>Uploading... {uploadProgress}%</span>
            </div>
          ) : (
            <span>{status}</span>
          )}
        </div>
      </div>
      
      {/* Violation Details Modal */}
      {showViolationDetails && (
        <div className="modal-overlay" onClick={() => setShowViolationDetails(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Violation Details</h3>
              <button className="close-btn" onClick={() => setShowViolationDetails(null)}>×</button>
            </div>
            <div className="modal-body">
              <div className="violation-detail">
                <div className="detail-row">
                  <span className="detail-label">Type:</span>
                  <span className="detail-value">{showViolationDetails.type}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Time:</span>
                  <span className="detail-value">{showViolationDetails.time}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Confidence:</span>
                  <span className={`detail-value confidence-${showViolationDetails.severity}`}>
                    {showViolationDetails.confidence}%
                  </span>
                </div>
                <div className="screenshot-preview">
                  <div className="screenshot-placeholder">
                    <span>Screenshot at {showViolationDetails.time}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;