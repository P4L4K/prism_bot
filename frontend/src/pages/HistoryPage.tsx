
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { RefreshCw, Trash2, MessageSquare, ChevronRight } from 'lucide-react';
import { motion } from 'framer-motion';
import { useAppStore } from '../store/useAppStore';

export const HistoryPage = () => {
  const { setCurrentBookId, setCurrentView } = useAppStore();

  const { data: books, isLoading, refetch } = useQuery({
    queryKey: ['history_books'],
    queryFn: async () => {
      const res = await axios.get('http://localhost:8000/api/history/books');
      return res.data;
    }
  });

  const clearHistory = async () => {
    if (confirm('Delete all history?')) {
      await axios.post('http://localhost:8000/api/history/clear');
      refetch();
    }
  };

  const handleOpenBook = (id: string) => {
    setCurrentBookId(id);
    setCurrentView('chat');
  };

  return (
    <div className="p-8 h-full flex flex-col bg-[var(--color-surface)]">
      <div className="flex items-center justify-between mb-8 shrink-0">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-2xl bg-orange-500/10 text-orange-500">
            <MessageSquare size={24} />
          </div>
          <div>
            <h2 className="text-3xl font-bold text-[var(--color-text-pri)] tracking-tight">Your Books</h2>
            <p className="text-[var(--color-text-sec)]">Past conversations and threads</p>
          </div>
        </div>

        <div className="flex gap-3">
          <button 
            onClick={() => refetch()} 
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[var(--color-chip)] hover:bg-[var(--color-border-card)] transition-colors text-[var(--color-text-pri)] text-sm font-medium"
          >
            <RefreshCw size={16} />
            Refresh
          </button>
          <button 
            onClick={clearHistory}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-red-500/10 text-red-500 hover:bg-red-500/20 transition-colors text-sm font-medium"
          >
            <Trash2 size={16} />
            Clear All
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto pr-4 scrollbar-thin">
        {isLoading ? (
          <div className="flex items-center justify-center h-full text-[var(--color-text-muted)]">
            <RefreshCw className="animate-spin mr-2" /> Loading your books...
          </div>
        ) : books?.length === 0 ? (
          <div className="flex items-center justify-center h-full text-[var(--color-text-muted)]">
            No history yet. Start a new book!
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {books?.map((book: any, idx: number) => (
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}
                key={book.id}
                onClick={() => handleOpenBook(book.id)}
                className="group relative glass-card p-6 rounded-3xl border border-[var(--color-border-card)] hover:border-[var(--color-primary)] hover:shadow-lg hover:shadow-[var(--color-primary)]/10 cursor-pointer transition-all duration-300 flex flex-col h-40"
              >
                <div className="flex justify-between items-start mb-auto">
                  <h3 className="font-semibold text-[var(--color-text-pri)] line-clamp-2 pr-4">{book.title}</h3>
                  <div className="opacity-0 group-hover:opacity-100 transition-opacity p-2 bg-[var(--color-primary)]/10 text-[var(--color-primary)] rounded-full shrink-0">
                    <ChevronRight size={16} />
                  </div>
                </div>
                
                <div className="flex items-center justify-between mt-4 pt-4 border-t border-[var(--color-border-subtle)] text-xs text-[var(--color-text-muted)]">
                  <span>{new Date(book.last_updated).toLocaleString()}</span>
                  <span className="bg-[var(--color-chip)] px-2 py-1 rounded-md">{book.message_count} msgs</span>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
