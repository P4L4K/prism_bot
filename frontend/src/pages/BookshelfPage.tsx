import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { RefreshCw, Trash2, BookPlus, Edit2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAppStore } from '../store/useAppStore';

export const BookshelfPage = () => {
  const { setCurrentBookId, setCurrentView } = useAppStore();
  const [openingBookId, setOpeningBookId] = useState<string | null>(null);

  const { data: books, isLoading, refetch } = useQuery({
    queryKey: ['history_books'],
    queryFn: async () => {
      const res = await axios.get('/api/history/books');
      return res.data;
    }
  });

  const clearHistory = async () => {
    if (confirm('Burn the bookshelf? All stories will be lost!')) {
      await axios.post('/api/history/clear');
      refetch();
    }
  };

  const handleOpenBook = (id: string) => {
    setOpeningBookId(id);
    // Add a slight delay for the opening animation
    setTimeout(() => {
      setCurrentBookId(id);
      setCurrentView('chat');
    }, 600);
  };

  const handleNewBook = () => {
    setCurrentBookId(crypto.randomUUID());
    setCurrentView('chat');
  };

  const handleRename = async (e: React.MouseEvent, id: string, oldTitle: string) => {
    e.stopPropagation();
    const newTitle = window.prompt("Enter a new title for this story:", oldTitle);
    if (newTitle && newTitle.trim()) {
      try {
        await axios.post('/api/history/rename', {
          session_id: id,
          title: newTitle.trim()
        });
        refetch();
      } catch (err) {
        console.error("Failed to rename book", err);
      }
    }
  };

  // Generate a random pastel color for each book cover based on its ID
  const getBookColor = (id: string) => {
    const colors = ['#E4A0B7', '#86A89D', '#D4B5B0', '#A3B1C6', '#C7B198'];
    const charCode = id.charCodeAt(id.length - 1) || 0;
    return colors[charCode % colors.length];
  };

  return (
    <div className="h-full w-full bg-[var(--color-sidebar)] overflow-y-auto relative p-12 scrollbar-thin">
      {/* Decorative background elements */}
      <div className="absolute top-0 left-0 w-full h-full opacity-10 pointer-events-none" 
           style={{ backgroundImage: 'radial-gradient(circle, #3D3935 1px, transparent 1px)', backgroundSize: '30px 30px' }} />
      
      <div className="max-w-6xl mx-auto relative z-10">
        
        {/* Header Header */}
        <div className="flex items-center justify-between mb-16">
          <div className="flex flex-col">
            <h1 className="text-5xl font-handwritten text-[var(--color-text-pri)] mb-2">My Bookshelf</h1>
            <p className="text-[var(--color-text-sec)] font-serif italic">Every conversation is a new story...</p>
          </div>

          <div className="flex gap-4">
            <button 
              onClick={handleNewBook}
              className="flex items-center gap-2 px-5 py-3 rounded-xl bg-[var(--color-primary)] text-white hover:bg-[var(--color-primary-light)] transition-all shadow-md hover:-translate-y-1"
            >
              <BookPlus size={20} />
              <span className="font-semibold">Write a New Story</span>
            </button>
            <button 
              onClick={clearHistory}
              className="flex items-center gap-2 px-5 py-3 rounded-xl bg-red-500/10 text-red-700 hover:bg-red-500/20 transition-all font-semibold"
            >
              <Trash2 size={20} />
            </button>
          </div>
        </div>

        {/* Bookshelf Render */}
        {isLoading ? (
          <div className="flex justify-center items-center h-64 text-[var(--color-text-sec)]">
            <RefreshCw className="animate-spin mr-3" /> Dusting the shelves...
          </div>
        ) : (
          <div className="flex flex-wrap gap-x-12 gap-y-24 justify-center md:justify-start">
            <AnimatePresence>
              {books?.map((book: any, idx: number) => {
                const coverColor = getBookColor(book.id);
                const isOpening = openingBookId === book.id;

                return (
                  <motion.div
                    key={book.id}
                    initial={{ opacity: 0, y: 50, rotateX: -20 }}
                    animate={{ 
                      opacity: isOpening ? 0 : 1, 
                      y: 0, 
                      rotateX: 0,
                      scale: isOpening ? 1.5 : 1,
                      zIndex: isOpening ? 50 : 1
                    }}
                    transition={{ delay: idx * 0.05, duration: 0.5, type: 'spring' }}
                    onClick={() => handleOpenBook(book.id)}
                    className="relative cursor-pointer group w-48 h-64"
                    style={{ perspective: 1000 }}
                  >
                    {/* The Book */}
                    <div 
                      className="absolute inset-0 shadow-2xl transition-transform duration-300 group-hover:-translate-y-4"
                      style={{ 
                        backgroundColor: coverColor,
                        borderRadius: '4px 12px 12px 4px',
                        borderLeft: '1px solid rgba(255,255,255,0.3)',
                        borderTop: '1px solid rgba(255,255,255,0.3)',
                        boxShadow: 'inset 4px 0 10px rgba(0,0,0,0.1), 5px 10px 20px rgba(0,0,0,0.2)',
                        transformStyle: 'preserve-3d'
                      }}
                    >
                      {/* Spine Texture */}
                      <div className="book-spine" />

                      {/* Cover Details */}
                      <div className="absolute inset-0 p-5 pl-8 flex flex-col justify-between">
                        <div className="bg-white/80 backdrop-blur-sm p-3 rounded-md shadow-sm border border-white/50 text-center transform -rotate-2 mt-4 relative group/title">
                          <h3 className="font-serif font-bold text-[var(--color-text-pri)] line-clamp-3 text-sm leading-tight">
                            {book.title || "Untitled Story"}
                          </h3>
                          <button 
                            onClick={(e) => handleRename(e, book.id, book.title)}
                            className="absolute -top-2 -right-2 bg-white rounded-full p-1 shadow-md text-gray-500 hover:text-blue-500 opacity-0 group-hover/title:opacity-100 transition-opacity"
                          >
                            <Edit2 size={12} />
                          </button>
                        </div>
                        
                        <div className="text-center mb-2">
                          <span className="inline-block bg-black/10 text-black/60 px-2 py-1 rounded text-xs font-bold uppercase tracking-widest backdrop-blur-sm">
                            {book.message_count} Pages
                          </span>
                        </div>
                      </div>

                      {/* Bookmark/Ribbon protruding */}
                      <div className="absolute -bottom-4 right-8 w-4 h-12 bg-red-400 shadow-sm" style={{ clipPath: 'polygon(0 0, 100% 0, 100% 100%, 50% 80%, 0 100%)' }} />
                    </div>

                    {/* Shelf Wood Planks (rendered below each row) */}
                    <div className="absolute -bottom-4 -left-6 -right-6 h-4 bg-[#8b7355] rounded-sm shadow-md" style={{ transform: 'translateZ(-10px)' }}>
                      <div className="absolute inset-0 opacity-20" style={{ backgroundImage: 'repeating-linear-gradient(90deg, transparent, transparent 10px, rgba(0,0,0,0.1) 10px, rgba(0,0,0,0.1) 20px)' }} />
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>
            
            {books?.length === 0 && (
              <div className="w-full text-center py-20">
                <p className="text-2xl font-handwritten text-[var(--color-text-muted)]">Your bookshelf is empty.</p>
                <p className="text-[var(--color-text-sec)] font-serif mt-2">Why not start writing your first story?</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
