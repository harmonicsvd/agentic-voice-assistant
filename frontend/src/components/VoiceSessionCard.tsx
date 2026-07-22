import { useState } from 'react';
import { PipecatClient } from '@pipecat-ai/client-js';

interface VoiceSessionCardProps {
  userSub: string;
  client: PipecatClient;
}

interface Meeting {
  title: string;
  name: string;
  date: string;
  time: string;
}

export const VoiceSessionCard = ({ userSub, client }: VoiceSessionCardProps) => {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [status, setStatus] = useState('');
  const [btnLabel, setBtnLabel] = useState('Tap to start call');
  const [btnHint, setBtnHint] = useState('Speak naturally — the agent will guide you');
  
  const [isConnected, setIsConnected] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  const toggleRecording = async () => {
    if (isRecording) {
      await stopRecording();
    } else {
      await startRecording();
    }
  };

  const startRecording = async () => {
    try {
      setIsLoading(true);
      setStatus('Connecting...');

      if (!client) {
        setStatus('Client not available');
        return;
      }

      await client.connect();
      
      setIsConnected(true);
      setIsRecording(true);
      setBtnLabel('Tap to end call');
      setBtnHint('Listening...');
      setStatus('Listening...');
    } catch (err) {
      console.error(err);
      setStatus('Failed');
    } finally {
      setIsLoading(false);
    }
  };

  const stopRecording = async () => {
    try {
      if (!client) return;

      await client.disconnect();
      setIsConnected(false);
      setIsRecording(false);
      setStatus('Disconnected');
      setBtnLabel('Tap to start call');
      setBtnHint('Speak naturally');
    } catch (err) {
      console.error(err);
    }
  };

  const addMeeting = (result: string) => {
    const titleMatch = result.match(/['"](.+?)['"]/);
    const dateMatch = result.match(/on (\d{4}-\d{2}-\d{2})/);
    const timeMatch = result.match(/at (\d{2}:\d{2})/);
    const nameMatch = result.match(/for (.+?) on/);

    const newMeeting: Meeting = {
      title: titleMatch ? titleMatch[1] : 'Meeting',
      date: dateMatch ? dateMatch[1] : '',
      time: timeMatch ? timeMatch[1] : '',
      name: nameMatch ? nameMatch[1] : 'Guest',
    };

    setMeetings((prev) => [newMeeting, ...prev].slice(0, 5));
  };

  const transcript = '';
  const responseText = '';

  return (
    <section className="panel">
      <div className="card">
        <div className="card-kicker">Live Assistant</div>
        <h2 className="card-title">Voice Session</h2>
        <p className="card-copy">Tap the mic, speak your request, and Ram will guide the rest.</p>

        <div className="voice-block">
          <div className="btn-wrap" onClick={toggleRecording}>
            <div className={`ring ring-1 ${isRecording ? 'active' : ''}`}></div>
            <div className={`ring ring-2 ${isRecording ? 'active' : ''}`}></div>
            <div className={`mic-btn ${isRecording ? 'active' : ''} ${isLoading ? 'loading' : ''}`}>
              <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#0f766e" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/>
                <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                <line x1="12" y1="19" x2="12" y2="22"/>
              </svg>
            </div>
          </div>

          <p className="btn-label">{btnLabel}</p>
          <p className="btn-hint">{btnHint}</p>
          <p className={`status ${status.includes('error') ? 'error' : status.includes('Connected') || status.includes('Listening') ? 'active' : ''}`}>
            {status}
          </p>
         
          {transcript && (
            <p className="transcript">You: {transcript}</p>
          )}
          {responseText && (
            <p className="response">AI: {responseText}</p>
          )}
        </div>

        <div className="meetings-box">
          <div className="meetings-title">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#0f766e" strokeWidth="2.5">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
            Recent Meetings
          </div>
          <div id="meetingsList">
            {meetings.length === 0 ? (
              <div className="no-meetings">No meetings scheduled yet</div>
            ) : (
              meetings.map((meeting, i) => (
                <div key={i} className="meeting-row">
                  <div className="meeting-dot"></div>
                  <div className="meeting-info">
                    <div className="meeting-name">{meeting.title}</div>
                    <div className="meeting-meta">{meeting.name} · {meeting.date}</div>
                  </div>
                  <div className="meeting-time">{meeting.time}</div>
                </div>
              ))
            )}
          </div>
        </div>

        <p className="footer">Powered by Open Source Voice Stack · Google Calendar · Mistral 7B</p>
      </div>
    </section>
  );
};
