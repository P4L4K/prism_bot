import React, { useState, useEffect, useRef } from 'react';
import { useAppStore, type ChatTurn } from '../store/useAppStore';
import { Mic, ArrowRight } from 'lucide-react';
import axios from 'axios';
import * as PageFlip from 'react-pageflip';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

const HTMLFlipBook: any = (PageFlip as any).default ? (PageFlip as any).default : PageFlip;

interface PageData {
  id: string;
  type: 'title' | 'content';
  content: string;
  pageNumber: number;
}

export const StorybookDashboard = () => {
  const { currentBookId, chatHistory, setChatHistory, liveTranscript, isListening, isSpeaking, isThinking, setIsThinking, addChatTurn, setIsListening } = useAppStore();
  const [inputText, setInputText] = useState('');
  const bookRef = useRef<any>(null);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await axios.get(`http://localhost:8000/api/history?limit=50&session_id=${currentBookId}`);
        const turns = res.data.reverse();
        const history: ChatTurn[] = [];
        turns.forEach((t: any) => {
          if (t.user_input) {
            history.push({ id: t.id + '-u', role: 'user', text: t.user_input, timestamp: t.timestamp });
          }
          if (t.assistant_response) {
            history.push({ id: t.id + '-a', role: 'assistant', text: t.assistant_response, timestamp: t.timestamp });
          }
        });
        setChatHistory(history);
      } catch (err) {
        console.error('Failed to load history', err);
      }
    };
    fetchHistory();
  }, [currentBookId]);

  const handleSend = async () => {
    if (!inputText.trim()) return;
    const textToSend = inputText.trim();
    
    setIsThinking(true);
    
    useAppStore.getState().addChatTurn({
      id: Date.now().toString() + '-user',
      role: 'user',
      text: textToSend,
      timestamp: new Date().toISOString(),
    });
    
    setInputText('');
    
    try {
      await axios.post('http://localhost:8000/api/chat', { text: textToSend, session_id: currentBookId, is_typed: true });
    } catch (e) {
      console.error(e);
    }
  };

  const handleListen = async () => {
    try {
      await axios.post('http://localhost:8000/api/listen', { session_id: currentBookId });
    } catch (e) {
      console.error(e);
    }
  };

  // Convert ChatHistory to Pages
  const activePages: PageData[] = [];
  
  // Page 0: Cover Page (Right side when closed)
  activePages.push({
    id: `cover-${currentBookId}`,
    type: 'title',
    content: currentBookId === 'default' ? 'The Book of Beginnings' : `Tale of ${currentBookId}`,
    pageNumber: 0
  });

  // Page 1: Inside Cover (Left side, usually blank)
  activePages.push({
    id: 'inside-cover',
    type: 'content',
    content: '',
    pageNumber: 1
  });

  // Page 2: Welcome Message (Right side)
  activePages.push({
    id: 'welcome-message',
    type: 'title',
    content: 'Welcome to your story. What shall we write today?',
    pageNumber: 2
  });

  let pageCounter = 3;

  chatHistory.forEach((turn) => {
    if (turn.role === 'user') {
      // User messages MUST go on Odd indices (Left page)
      if (activePages.length % 2 === 0) {
        activePages.push({ id: `pad-${turn.id}`, type: 'content', content: '', pageNumber: pageCounter++ });
      }
      activePages.push({
        id: turn.id,
        type: 'title',
        content: turn.text,
        pageNumber: pageCounter++
      });
    } else {
      // Assistant responses MUST go on Even indices (Right page)
      if (activePages.length % 2 !== 0) {
        activePages.push({ id: `pad-${turn.id}`, type: 'content', content: '', pageNumber: pageCounter++ });
      }
      activePages.push({
        id: turn.id,
        type: 'content',
        content: turn.text,
        pageNumber: pageCounter++
      });
    }
  });

  if (isThinking) {
    if (activePages.length % 2 !== 0) {
      activePages.push({ id: 'pad-thinking', type: 'content', content: '', pageNumber: pageCounter++ });
    }
    activePages.push({
      id: 'thinking',
      type: 'content',
      content: '*The quill is writing...*', // Rendered as markdown
      pageNumber: pageCounter++
    });
  }

  // Auto-flip to the latest page whenever new content is added
  useEffect(() => {
    if (bookRef.current && activePages.length > 0) {
      setTimeout(() => {
        try {
          const flipApi = bookRef.current.pageFlip();
          if (flipApi) {
             const targetIdx = activePages.length - 1;
             // Only flip if we are not already at the end
             if (flipApi.getCurrentPageIndex() < targetIdx - 1) {
                flipApi.flip(targetIdx);
             }
          }
        } catch (e) {
          console.error("Page flip error:", e);
        }
      }, 150);
    }
  }, [activePages.length]);
  
  const MAX_PAGES = 50;
  
  // We MUST render a fixed number of DOM nodes to prevent React 19 from crashing 
  // when react-pageflip mutates the DOM tree. 
  const renderedPages = [];
  for (let i = 0; i < MAX_PAGES; i++) {
    const page = activePages[i];
    renderedPages.push(
      <div key={`fixed-page-${i}`} className="page paper-texture border border-[var(--color-border-card)] relative overflow-hidden bg-[var(--color-background)]">
        {/* Decorative Washi Tape */}
        {i % 3 === 0 && <div className="washi-tape top-4 left-4 h-8 w-24" />}
        {i % 4 === 0 && <div className="washi-tape bottom-4 right-10 h-8 w-32 bg-blue-200/50" />}

        {page ? (
          <div className="p-12 h-full flex flex-col">
            {page.type === 'title' ? (
              <div className="flex-1 flex flex-col items-center justify-center text-center">
                <h2 className="text-3xl font-handwritten text-[var(--color-text-sec)] mb-8 whitespace-pre-wrap">
                  {page.content}
                </h2>
                {i === activePages.length - 1 && liveTranscript && (
                    <p className="text-xl font-handwritten text-[var(--color-primary-light)] animate-pulse mt-4">
                      {liveTranscript}...
                    </p>
                )}
              </div>
            ) : (
              <div className="flex-1 overflow-y-auto scrollbar-thin prose prose-stone prose-sm md:prose-base max-w-none text-[var(--color-text-pri)] pr-2">
                {page.id === 'thinking' ? (
                  <div className="animate-pulse flex items-center gap-2 font-handwritten text-2xl text-[var(--color-primary-light)]">
                    The quill is writing
                    <span className="animate-bounce">.</span>
                    <span className="animate-bounce" style={{animationDelay: '0.2s'}}>.</span>
                    <span className="animate-bounce" style={{animationDelay: '0.4s'}}>.</span>
                  </div>
                ) : (
                  <ReactMarkdown 
                    components={{
                      code({node, inline, className, children, ...props}: any) {
                        const match = /language-(\w+)/.exec(className || '')
                        return !inline && match ? (
                          <div className="relative my-4 transform -rotate-1 shadow-md bg-zinc-900 rounded-lg p-2 overflow-hidden border-2 border-[var(--color-border-card)]">
                              <div className="absolute top-2 right-2 washi-tape bg-yellow-200/60 w-12 h-6" />
                              <SyntaxHighlighter
                                style={vscDarkPlus as any}
                                language={match[1]}
                                PreTag="div"
                                {...props}
                              >
                                {String(children).replace(/\n$/, '')}
                              </SyntaxHighlighter>
                          </div>
                        ) : (
                          <code className="bg-orange-100 px-1 py-0.5 rounded text-orange-800 font-handwritten text-lg" {...props}>
                            {children}
                          </code>
                        )
                      }
                    }}
                  >
                    {page.content}
                  </ReactMarkdown>
                )}
              </div>
            )}
            
            {/* Page Numbering */}
            <div className="mt-auto pt-4 flex justify-between items-end text-[var(--color-text-muted)] font-serif text-sm border-t border-[var(--color-border-card)]">
              <span>{i % 2 === 0 ? `Page ${page.pageNumber}` : ''}</span>
              <span>{i % 2 !== 0 ? `Page ${page.pageNumber}` : ''}</span>
            </div>
          </div>
        ) : (
          <div className="p-12 h-full flex flex-col opacity-20">
            <div className="flex-1 flex flex-col items-center justify-center">
            </div>
            <div className="mt-auto pt-4 flex justify-between items-end text-[var(--color-text-muted)] font-serif text-sm border-t border-[var(--color-border-card)]">
              <span>{i % 2 === 0 ? `Page ${i + 1}` : ''}</span>
              <span>{i % 2 !== 0 ? `Page ${i + 1}` : ''}</span>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-[var(--color-background)] items-center justify-center p-8 relative overflow-hidden">
      
      {/* Mascot Area */}
      <div className="absolute top-10 right-10 w-24 h-24 z-0 opacity-80">
        <div className="bg-white/50 backdrop-blur-sm rounded-full p-4 shadow-sm border border-white flex items-center justify-center">
            {isSpeaking ? '🦊 Speaking...' : isListening ? '🦊 Listening...' : '🦊 Idle'}
        </div>
      </div>

      <div className="w-full max-w-5xl h-[80vh] flex items-center justify-center relative z-10 perspective-1000">
        <HTMLFlipBook 
          width={500} 
          height={700} 
          size="stretch"
          minWidth={315}
          maxWidth={1000}
          minHeight={400}
          maxHeight={1533}
          maxShadowOpacity={0.5}
          showCover={true}
          mobileScrollSupport={true}
          startZIndex={0}
          autoSize={true}
          showPageCorners={true}
          disableFlipByClick={false}
          className="storybook shadow-2xl"
          ref={bookRef}
          style={{ margin: '0 auto' }}
          usePortrait={false}
          startPage={0}
          drawShadow={true}
          flippingTime={1000}
          useMouseEvents={true}
          swipeDistance={30}
          clickEventForward={true}
        >
          {renderedPages}
        </HTMLFlipBook>
      </div>

      {/* Centered Input Area */}
      <div className="relative z-50 flex flex-col items-center gap-2 group mt-6">
        <div className="bg-white/90 backdrop-blur-xl p-4 rounded-3xl shadow-2xl border border-[var(--color-border-card)] flex items-center gap-3 w-[600px] max-w-[90vw]">
          <button 
            onClick={handleListen}
            className={`w-12 h-12 rounded-full flex items-center justify-center shrink-0 transition-all ${
              isListening 
                ? 'bg-red-500 text-white animate-pulse shadow-lg shadow-red-500/30' 
                : 'bg-[var(--color-surface)] text-[var(--color-text-sec)] hover:bg-[var(--color-primary-soft)] hover:text-[var(--color-primary)]'
            }`}
          >
            <Mic size={20} />
          </button>
          
          <input 
            type="text" 
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder={isListening ? "Speak to the Story..." : "Write your next prompt..."}
            className="flex-1 bg-transparent border-none text-[var(--color-text-pri)] focus:ring-0 font-handwritten text-xl placeholder:text-[var(--color-text-muted)] w-full"
          />
          
          <button 
            onClick={handleSend}
            className="flex items-center gap-2 px-4 py-2 rounded-2xl bg-[var(--color-primary)] text-white hover:bg-[var(--color-primary-light)] font-bold text-sm shrink-0"
          >
            Turn Page <ArrowRight size={16} />
          </button>
        </div>
      </div>

    </div>
  );
};
