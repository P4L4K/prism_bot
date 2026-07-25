import { useEffect, useState } from 'react';
import axios from 'axios';
import { Save } from 'lucide-react';
import { motion } from 'framer-motion';

export const SettingsPage = () => {
  const [settings, setSettings] = useState<any>({});
  const [saving, setSaving] = useState(false);
  const [citySuggestions, setCitySuggestions] = useState<string[]>([]);

  useEffect(() => {
    axios.get('http://localhost:8000/api/settings')
      .then(res => setSettings(res.data))
      .catch(console.error);
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      await axios.post('http://localhost:8000/api/settings', settings);
      alert('Settings saved successfully!');
    } catch (e) {
      console.error(e);
      alert('Failed to save settings.');
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (key: string, val: any) => {
    setSettings((prev: any) => ({ ...prev, [key]: val }));
  };

  const handleCityChange = async (val: string) => {
    handleChange('default_city', val);
    if (val.length > 2) {
      try {
        const res = await axios.get(`https://nominatim.openstreetmap.org/search?city=${val}&format=json&limit=5`);
        const cities = res.data.map((item: any) => item.display_name);
        setCitySuggestions(cities);
      } catch (e) {
        console.error(e);
      }
    } else {
      setCitySuggestions([]);
    }
  };

  return (
    <div className="p-8 h-full overflow-y-auto bg-[var(--color-surface)]">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-[var(--color-text-pri)] flex items-center gap-3">
            ⚙️ Settings
          </h1>
          <p className="text-[var(--color-text-muted)] mt-2">Configure PRISM to your liking</p>
        </div>
        <button 
          onClick={handleSave} 
          disabled={saving}
          className="flex items-center gap-2 px-6 py-3 rounded-xl bg-[var(--color-primary)] text-white hover:bg-[var(--color-primary-light)] transition-colors shadow-lg disabled:opacity-50"
        >
          <Save size={18} /> {saving ? 'Saving...' : 'Save Changes'}
        </button>
      </div>

      <div className="max-w-2xl space-y-6">
        <motion.div initial={{opacity: 0, y: 10}} animate={{opacity: 1, y: 0}} className="glass-card p-6 rounded-3xl">
          <h3 className="font-bold text-lg mb-4 text-[var(--color-text-pri)]">Voice Configuration</h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-[var(--color-text-sec)] mb-2">Speech Rate</label>
              <input 
                type="range" min="100" max="300" step="10" 
                value={settings.voice_rate || 200}
                onChange={e => handleChange('voice_rate', parseInt(e.target.value))}
                className="w-full accent-[var(--color-primary)]"
              />
              <div className="text-xs text-[var(--color-text-muted)] mt-1">{settings.voice_rate} WPM</div>
            </div>

            <div>
              <label className="block text-sm font-medium text-[var(--color-text-sec)] mb-2">Voice Volume</label>
              <input 
                type="range" min="0" max="1" step="0.1"
                value={settings.voice_volume || 1.0}
                onChange={e => handleChange('voice_volume', parseFloat(e.target.value))}
                className="w-full accent-[var(--color-primary)]"
              />
              <div className="text-xs text-[var(--color-text-muted)] mt-1">{Math.round((settings.voice_volume || 1) * 100)}%</div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-[var(--color-text-sec)] mb-2">STT Engine</label>
              <select 
                value={settings.stt_engine || 'google'}
                onChange={e => handleChange('stt_engine', e.target.value)}
                className="w-full p-3 rounded-xl bg-[var(--color-background)] border-none focus:ring-2 focus:ring-[var(--color-primary)] text-[var(--color-text-pri)]"
              >
                <option value="google">Google Web Speech (Cloud)</option>
                <option value="whisper">OpenAI Whisper (Local)</option>
              </select>
            </div>
          </div>
        </motion.div>

        <motion.div initial={{opacity: 0, y: 10}} animate={{opacity: 1, y: 0}} transition={{delay: 0.1}} className="glass-card p-6 rounded-3xl relative z-10">
          <h3 className="font-bold text-lg mb-4 text-[var(--color-text-pri)]">General Preferences</h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-[var(--color-text-sec)] mb-2">Temperature Unit</label>
              <select 
                value={settings.temperature_unit || 'celsius'}
                onChange={e => handleChange('temperature_unit', e.target.value)}
                className="w-full p-3 rounded-xl bg-[var(--color-background)] border-none focus:ring-2 focus:ring-[var(--color-primary)] text-[var(--color-text-pri)]"
              >
                <option value="celsius">Celsius (°C)</option>
                <option value="fahrenheit">Fahrenheit (°F)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-[var(--color-text-sec)] mb-2">News Category</label>
              <select 
                value={settings.news_category || 'technology'}
                onChange={e => handleChange('news_category', e.target.value)}
                className="w-full p-3 rounded-xl bg-[var(--color-background)] border-none focus:ring-2 focus:ring-[var(--color-primary)] text-[var(--color-text-pri)]"
              >
                <option value="general">General</option>
                <option value="technology">Technology</option>
                <option value="business">Business</option>
                <option value="science">Science</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-[var(--color-text-sec)] mb-2">News Area/Location</label>
              <input 
                type="text" 
                value={settings.news_location || ''}
                onChange={e => handleChange('news_location', e.target.value)}
                placeholder="e.g. New York, India, Silicon Valley (optional)"
                className="w-full p-3 rounded-xl bg-[var(--color-background)] border-none focus:ring-2 focus:ring-[var(--color-primary)] text-[var(--color-text-pri)]"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-[var(--color-text-sec)] mb-2">Default City</label>
              <div className="relative">
                <input 
                  type="text" 
                  value={settings.default_city || ''}
                  onChange={e => handleCityChange(e.target.value)}
                  placeholder="e.g. London"
                  className="w-full p-3 rounded-xl bg-[var(--color-background)] border-none focus:ring-2 focus:ring-[var(--color-primary)] text-[var(--color-text-pri)]"
                />
                {citySuggestions.length > 0 && (
                  <div className="absolute top-full left-0 right-0 mt-1 bg-white rounded-xl shadow-lg border border-[var(--color-border-card)] z-50 overflow-hidden">
                    {citySuggestions.map((city, idx) => (
                      <div 
                        key={idx} 
                        className="p-3 hover:bg-[var(--color-card-hover)] cursor-pointer text-sm border-b border-[var(--color-border-card)] last:border-0"
                        onClick={() => {
                          handleChange('default_city', city.split(',')[0]);
                          setCitySuggestions([]);
                        }}
                      >
                        {city}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </motion.div>

        <motion.div initial={{opacity: 0, y: 10}} animate={{opacity: 1, y: 0}} transition={{delay: 0.2}} className="glass-card p-6 rounded-3xl relative z-0">
          <h3 className="font-bold text-lg mb-4 text-[var(--color-text-pri)]">Wake Word Detection</h3>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-[var(--color-text-sec)]">Enable Hands-Free Wake Word</label>
              <input 
                type="checkbox" 
                checked={settings.wake_word_enabled || false}
                onChange={e => handleChange('wake_word_enabled', e.target.checked)}
                className="w-5 h-5 accent-[var(--color-primary)]"
              />
            </div>

            {settings.wake_word_enabled && (
              <div>
                <label className="block text-sm font-medium text-[var(--color-text-sec)] mb-2">Wake Word Model</label>
                <select 
                  value={settings.wake_word_model || 'alexa'}
                  onChange={e => handleChange('wake_word_model', e.target.value)}
                  className="w-full p-3 rounded-xl bg-[var(--color-background)] border-none focus:ring-2 focus:ring-[var(--color-primary)] text-[var(--color-text-pri)]"
                >
                  <option value="alexa">Alexa</option>
                  <option value="hey_jarvis">Hey Jarvis</option>
                  <option value="computer">Computer</option>
                  <option value="hey_mycroft">Hey Mycroft</option>
                </select>
              </div>
            )}
          </div>
        </motion.div>
      </div>
    </div>
  );
};
