# AAIS Advanced Features - Video, Streaming & Analytics

## Overview

This guide covers:
- Video processing and analysis
- Real-time streaming with WebSockets
- Advanced analytics and dashboards
- Performance tracking
- User behavior analytics

---

## 1. Video Processing

### Setup Video Processing Module

```python
# src/video_processor.py

import cv2
import numpy as np
from pathlib import Path
from src.logger import get_logger

logger = get_logger(__name__)

class VideoProcessor:
    """Video processing and analysis"""
    
    def __init__(self):
        """Initialize video processor"""
        self.supported_formats = ['.mp4', '.avi', '.mov', '.mkv']
    
    def extract_frames(self, video_path, interval=1):
        """Extract frames from video"""
        try:
            logger.info(f"Extracting frames from {video_path}")
            cap = cv2.VideoCapture(video_path)
            frames = []
            frame_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_count % interval == 0:
                    frames.append(frame)
                
                frame_count += 1
            
            cap.release()
            logger.info(f"Extracted {len(frames)} frames")
            return frames
        except Exception as e:
            logger.error(f"Error extracting frames: {e}")
            raise
    
    def get_video_info(self, video_path):
        """Get video metadata"""
        try:
            cap = cv2.VideoCapture(video_path)
            
            info = {
                'fps': cap.get(cv2.CAP_PROP_FPS),
                'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'duration': int(cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS))
            }
            
            cap.release()
            logger.info(f"Video info: {info}")
            return info
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            raise
    
    def analyze_motion(self, video_path):
        """Analyze motion in video"""
        try:
            logger.info(f"Analyzing motion in {video_path}")
            cap = cv2.VideoCapture(video_path)
            
            ret, prev_frame = cap.read()
            prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
            
            motion_data = []
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                flow = cv2.calcOpticalFlowFarneback(
                    prev_gray, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0
                )
                
                magnitude, angle = cv2.cartToPolar(flow[..., 0], flow[..., 1])
                motion_data.append({
                    'magnitude': float(magnitude.mean()),
                    'angle': float(angle.mean())
                })
                
                prev_gray = gray
            
            cap.release()
            logger.info(f"Motion analysis complete")
            return motion_data
        except Exception as e:
            logger.error(f"Error analyzing motion: {e}")
            raise
    
    def generate_thumbnail(self, video_path, output_path, timestamp=0):
        """Generate thumbnail from video"""
        try:
            logger.info(f"Generating thumbnail for {video_path}")
            cap = cv2.VideoCapture(video_path)
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_number = int(timestamp * fps)
            
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()
            
            if ret:
                thumbnail = cv2.resize(frame, (320, 180))
                cv2.imwrite(output_path, thumbnail)
                logger.info(f"Thumbnail saved to {output_path}")
            
            cap.release()
            return output_path
        except Exception as e:
            logger.error(f"Error generating thumbnail: {e}")
            raise
```

### Add Video API Endpoints

```python
# In src/main.py

from src.video_processor import VideoProcessor
import base64

video_processor = VideoProcessor()

@app.route('/api/video/analyze', methods=['POST'])
def analyze_video():
    """Analyze video"""
    try:
        if 'video' not in request.files:
            return jsonify({"error": "Video required"}), 400
        
        video_file = request.files['video']
        video_path = f"/tmp/{video_file.filename}"
        video_file.save(video_path)
        
        info = video_processor.get_video_info(video_path)
        motion = video_processor.analyze_motion(video_path)
        
        return jsonify({
            "info": info,
            "motion": motion
        })
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/video/thumbnail', methods=['POST'])
def generate_thumbnail():
    """Generate video thumbnail"""
    try:
        if 'video' not in request.files:
            return jsonify({"error": "Video required"}), 400
        
        timestamp = request.form.get('timestamp', 0, type=float)
        video_file = request.files['video']
        video_path = f"/tmp/{video_file.filename}"
        video_file.save(video_path)
        
        output_path = f"/tmp/thumbnail_{video_file.filename}.jpg"
        video_processor.generate_thumbnail(video_path, output_path, timestamp)
        
        with open(output_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode()
        
        return jsonify({"thumbnail": image_data, "format": "jpg"})
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500
```

---

## 2. Real-time Streaming with WebSockets

### Setup WebSocket Server

```python
# src/websocket_server.py

from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime
from src.logger import get_logger

logger = get_logger(__name__)

class StreamingServer:
    """WebSocket streaming server"""
    
    def __init__(self, app):
        """Initialize streaming server"""
        self.socketio = SocketIO(app, cors_allowed_origins="*")
        self.active_streams = {}
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            logger.info(f"Client connected")
            emit('response', {'data': 'Connected to streaming server'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            logger.info(f"Client disconnected")
        
        @self.socketio.on('start_stream')
        def handle_start_stream(data):
            """Start streaming"""
            stream_id = data.get('stream_id')
            logger.info(f"Starting stream: {stream_id}")
            
            self.active_streams[stream_id] = {
                'started_at': datetime.utcnow(),
                'frames': 0
            }
            
            emit('stream_started', {'stream_id': stream_id}, broadcast=True)
        
        @self.socketio.on('send_frame')
        def handle_frame(data):
            """Receive and broadcast frame"""
            stream_id = data.get('stream_id')
            if stream_id in self.active_streams:
                self.active_streams[stream_id]['frames'] += 1
                emit('frame', data, broadcast=True)
        
        @self.socketio.on('stop_stream')
        def handle_stop_stream(data):
            """Stop streaming"""
            stream_id = data.get('stream_id')
            if stream_id in self.active_streams:
                stream_info = self.active_streams[stream_id]
                logger.info(f"Stopping stream: {stream_id}")
                del self.active_streams[stream_id]
                emit('stream_stopped', {'frames': stream_info['frames']}, broadcast=True)
    
    def get_active_streams(self):
        """Get active streams"""
        return self.active_streams
```

### Add Streaming Endpoints

```python
# In src/main.py

from src.websocket_server import StreamingServer

streaming = StreamingServer(app)

@app.route('/api/streaming/status', methods=['GET'])
def streaming_status():
    """Get streaming status"""
    try:
        streams = streaming.get_active_streams()
        return jsonify({
            "active_streams": len(streams),
            "streams": [
                {
                    "stream_id": stream_id,
                    "frames": s['frames'],
                    "duration": (datetime.utcnow() - s['started_at']).total_seconds()
                }
                for stream_id, s in streams.items()
            ]
        })
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500
```

---

## 3. Analytics & Dashboards

### Setup Analytics Module

```python
# src/analytics.py

from datetime import datetime, timedelta
from src.database import GeneratedContent
from src.logger import get_logger
from sqlalchemy import func

logger = get_logger(__name__)

class Analytics:
    """Analytics and reporting"""
    
    @staticmethod
    def get_usage_stats(days=7):
        """Get usage statistics"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            stats = GeneratedContent.query.filter(
                GeneratedContent.created_at >= start_date
            ).all()
            
            by_type = {}
            for content in stats:
                content_type = content.content_type
                if content_type not in by_type:
                    by_type[content_type] = {'count': 0, 'total_time': 0}
                by_type[content_type]['count'] += 1
                by_type[content_type]['total_time'] += content.processing_time or 0
            
            return [
                {
                    'type': content_type,
                    'count': data['count'],
                    'avg_time': data['total_time'] / data['count'] if data['count'] > 0 else 0
                }
                for content_type, data in by_type.items()
            ]
        except Exception as e:
            logger.error(f"Error: {e}")
            raise
    
    @staticmethod
    def get_user_stats(user_id):
        """Get user statistics"""
        try:
            content = GeneratedContent.query.filter(
                GeneratedContent.user_id == user_id
            ).all()
            
            return {
                'total_generations': len(content),
                'by_type': {
                    'text': len([c for c in content if c.content_type == 'text']),
                    'image': len([c for c in content if c.content_type == 'image']),
                    'audio': len([c for c in content if c.content_type == 'audio']),
                    'video': len([c for c in content if c.content_type == 'video'])
                },
                'avg_processing_time': sum([c.processing_time or 0 for c in content]) / len(content) if content else 0
            }
        except Exception as e:
            logger.error(f"Error: {e}")
            raise
    
    @staticmethod
    def get_performance_metrics():
        """Get performance metrics"""
        try:
            content = GeneratedContent.query.all()
            
            if not content:
                return {}
            
            times = [c.processing_time for c in content if c.processing_time]
            
            return {
                'avg_response_time': sum(times) / len(times) if times else 0,
                'min_response_time': min(times) if times else 0,
                'max_response_time': max(times) if times else 0,
                'p95_response_time': sorted(times)[int(len(times) * 0.95)] if times else 0,
                'total_requests': len(content)
            }
        except Exception as e:
            logger.error(f"Error: {e}")
            raise
```

### Add Analytics Endpoints

```python
# In src/main.py

from src.analytics import Analytics

@app.route('/api/analytics/usage', methods=['GET'])
def get_usage_stats():
    """Get usage statistics"""
    try:
        days = request.args.get('days', 7, type=int)
        stats = Analytics.get_usage_stats(days)
        return jsonify({"stats": stats})
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/analytics/user/<int:user_id>', methods=['GET'])
def get_user_stats(user_id):
    """Get user statistics"""
    try:
        stats = Analytics.get_user_stats(user_id)
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/analytics/performance', methods=['GET'])
def get_performance():
    """Get performance metrics"""
    try:
        metrics = Analytics.get_performance_metrics()
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500
```

---

## 4. Analytics Dashboard (Frontend)

### Create Analytics Dashboard Component

```jsx
// frontend/src/pages/AnalyticsDashboard.jsx

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './AnalyticsDashboard.css';

function AnalyticsDashboard() {
  const [usageStats, setUsageStats] = useState([]);
  const [performanceMetrics, setPerformanceMetrics] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const [usage, performance] = await Promise.all([
        axios.get('http://localhost:5000/api/analytics/usage?days=7'),
        axios.get('http://localhost:5000/api/analytics/performance')
      ]);

      setUsageStats(usage.data.stats);
      setPerformanceMetrics(performance.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading analytics...</div>;
  }

  return (
    <div className="analytics-dashboard">
      <h1>Analytics Dashboard</h1>

      <div className="metrics-grid">
        <div className="metric-card">
          <h3>Total Requests</h3>
          <p className="metric-value">{performanceMetrics.total_requests || 0}</p>
        </div>
        <div className="metric-card">
          <h3>Avg Response Time</h3>
          <p className="metric-value">{(performanceMetrics.avg_response_time || 0).toFixed(2)}ms</p>
        </div>
        <div className="metric-card">
          <h3>P95 Response Time</h3>
          <p className="metric-value">{(performanceMetrics.p95_response_time || 0).toFixed(2)}ms</p>
        </div>
        <div className="metric-card">
          <h3>Max Response Time</h3>
          <p className="metric-value">{(performanceMetrics.max_response_time || 0).toFixed(2)}ms</p>
        </div>
      </div>

      <div className="usage-section">
        <h2>Usage by Type (Last 7 Days)</h2>
        <div className="usage-grid">
          {usageStats.map((stat, index) => (
            <div key={index} className="usage-card">
              <h3>{stat.type.toUpperCase()}</h3>
              <p className="usage-count">{stat.count} generations</p>
              <p className="usage-time">Avg: {stat.avg_time.toFixed(2)}ms</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default AnalyticsDashboard;
```

---

## 5. Dependencies

```bash
# Add to requirements.txt
opencv-python>=4.5.0
opencv-contrib-python>=4.5.0
python-socketio>=5.5.0
python-engineio>=4.3.0
python-dateutil>=2.8.0
```

---

## 6. Performance Targets

- Video processing: < 5 seconds per minute of video
- Streaming latency: < 500ms
- Analytics queries: < 1 second
- Dashboard load: < 2 seconds

---

## 7. Feature Checklist

- [ ] Video processing module
- [ ] Motion analysis
- [ ] Thumbnail generation
- [ ] WebSocket streaming
- [ ] Real-time frame broadcasting
- [ ] Analytics collection
- [ ] Performance metrics
- [ ] User statistics
- [ ] Analytics dashboard
- [ ] Usage reports
- [ ] Performance monitoring

---

## Support

- OpenCV: https://opencv.org/
- Socket.IO: https://socket.io/
- Flask-SocketIO: https://flask-socketio.readthedocs.io/
