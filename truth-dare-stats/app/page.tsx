'use client';

import { useState, FC, FormEvent, ReactNode } from 'react';
import { Search, BarChart, Users, Gamepad2, Crown, Star, History, Swords, Shield, Bot, User, Hash, X, ClipboardList, Trophy, UserCog } from 'lucide-react';

// --- Type Definitions ---
interface Player { name: string; username?: string; score: number; truths: number; dares: number; }
interface GameHistory { game_name: string; start_time: string; winner: string; scores: Record<string, number>; }
interface GroupStats { groupName: string; totalGames: number; highestScore: number; uniquePlayers: number; topPlayers: Player[]; gameHistory: GameHistory[]; }
interface UserStatsData {
  name: string;
  username?: string;
  stats: { games_played: number; total_score: number; highest_score: number; total_truths: number; total_dares: number; total_skips: number; };
  groups_played: { id: number; name: string }[];
}
type Page = 'home' | 'stats' | 'learn';


// --- Reusable Components ---
interface StatCardProps { icon: ReactNode; label: string; value: number | string; color: string; }
const StatCard: FC<StatCardProps> = ({ icon, label, value, color }) => (
  <div className="bg-gray-800/50 p-6 rounded-xl flex items-center space-x-4 border border-white/10">
    <div className={`p-3 rounded-lg ${color}`}>{icon}</div>
    <div><p className="text-sm text-gray-400">{label}</p><p className="text-2xl font-bold text-white">{value}</p></div>
  </div>
);
interface PlayerRowProps extends Player { rank: number; }
const PlayerRow: FC<PlayerRowProps> = ({ rank, name, username, score, truths, dares }) => {
  const rankColor: Record<number, string> = { 1: 'text-yellow-400', 2: 'text-gray-300', 3: 'text-amber-500' };
  return (
    <div className="flex items-center p-4 bg-gray-800/60 rounded-lg mb-3 hover:bg-gray-700/80 transition-colors duration-300">
      <div className={`w-8 text-lg font-bold ${rankColor[rank] || 'text-gray-500'}`}>#{rank}</div>
      <div className="flex-1 font-semibold text-white truncate pr-2">{name} {username && <span className="text-sm text-gray-400 ml-1 hidden sm:inline">@{username}</span>}</div>
      <div className="flex items-center space-x-2 sm:space-x-4 text-xs sm:text-sm text-gray-300">
        <div className="flex items-center" title="Total Score"><Star className="w-4 h-4 mr-1 text-yellow-400" /><span>{score}</span></div>
        <div className="flex items-center" title="Truths Completed"><Swords className="w-4 h-4 mr-1 text-blue-400" /><span>{truths}</span></div>
        <div className="flex items-center" title="Dares Completed"><Shield className="w-4 h-4 mr-1 text-red-400" /><span>{dares}</span></div>
      </div>
    </div>
  );
};
const GameHistoryCard: FC<GameHistory> = ({ game_name, start_time, winner }) => {
    const formattedDateTime = new Date(start_time).toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit', hour12: true });
    return (
        <div className="bg-gray-800/60 p-4 rounded-lg border border-white/10 transform hover:scale-105 transition-transform duration-300">
            <div className="flex justify-between items-start mb-2"><h3 className="font-bold text-white pr-2">{game_name}</h3><p className="text-xs text-gray-400 text-right flex-shrink-0">{formattedDateTime}</p></div>
            <div className="text-sm text-gray-300"><p className="flex items-center"><Crown className="w-4 h-4 mr-2 text-yellow-400"/>Winner: <span className="font-semibold ml-1">{winner}</span></p></div>
        </div>
    );
};
const UserStatsDisplay: FC<{ data: UserStatsData }> = ({ data }) => (
    <div className="animate-fade-in">
        <h2 className="text-2xl font-bold mb-6 text-center text-gray-300">
            Displaying Stats for: <span className="text-indigo-400">{data.name}</span>
            {data.username && <span className="text-gray-400 text-lg ml-2">@{data.username}</span>}
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-6 mb-12">
            <StatCard icon={<Gamepad2 size={24}/>} label="Games Played" value={data.stats.games_played} color="bg-indigo-500/80" />
            <StatCard icon={<Star size={24}/>} label="Total Score" value={data.stats.total_score} color="bg-green-500/80" />
            <StatCard icon={<Crown size={24}/>} label="Highest Score" value={data.stats.highest_score} color="bg-yellow-500/80" />
            <StatCard icon={<Swords size={24}/>} label="Total Truths" value={data.stats.total_truths} color="bg-blue-500/80" />
            <StatCard icon={<Shield size={24}/>} label="Total Dares" value={data.stats.total_dares} color="bg-red-500/80" />
            <StatCard icon={<History size={24}/>} label="Total Skips" value={data.stats.total_skips} color="bg-gray-500/80" />
        </div>
        <div>
            <h3 className="text-xl font-semibold mb-4 flex items-center"><Users className="mr-2"/> Groups Played In</h3>
            <div className="space-y-2">
                {data.groups_played.map(group => ( <div key={group.id} className="bg-gray-800/60 p-3 rounded-lg text-sm">{group.name}</div> ))}
            </div>
        </div>
    </div>
);

// --- Home Page Components ---
const BOT_USERNAME = "YourBotUsername"; // <-- IMPORTANT: Change this to your bot's actual username

const HeroSection: FC<{ onNavigate: (page: Page) => void }> = ({ onNavigate }) => (
    <div className="text-center py-16 sm:py-20">
        <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent mb-4">
            The Ultimate Truth or Dare Bot
        </h1>
        <p className="text-md sm:text-lg text-gray-400 max-w-2xl mx-auto mb-8">
            Bring your Telegram groups to life with a fully automated, feature-rich Truth or Dare game. Track scores, view history, and compete with friends.
        </p>
        <div className="flex flex-col sm:flex-row justify-center items-center space-y-4 sm:space-y-0 sm:space-x-4">
            <a href={`https://t.me/CosmicTandDBot`} target="_blank" rel="noopener noreferrer" className="inline-flex items-center px-6 py-3 bg-blue-600 rounded-full text-base font-semibold hover:bg-blue-500 transition-colors transform hover:scale-105 w-full sm:w-auto justify-center"><Bot className="w-5 h-5 mr-2" />Add Bot to Group</a>
            <button onClick={() => onNavigate('stats')} className="inline-flex items-center px-6 py-3 bg-gray-700/50 rounded-full text-base font-semibold hover:bg-gray-700/80 transition-colors w-full sm:w-auto justify-center"><BarChart className="w-5 h-5 mr-2" />View Stats</button>
        </div>
    </div>
);

const FeatureCard: FC<{ icon: ReactNode, title: string, children: ReactNode }> = ({ icon, title, children }) => (
    <div className="bg-gray-800/50 p-6 rounded-xl border border-white/10">
        <div className="flex items-center mb-4"><div className="p-2 bg-indigo-500/80 rounded-lg mr-4">{icon}</div><h3 className="text-xl font-bold">{title}</h3></div>
        <p className="text-gray-400">{children}</p>
    </div>
);

const FeaturesSection = () => (
    <div className="py-10">
        <h2 className="text-3xl font-bold text-center mb-12">Why Choose Our Bot?</h2>
        <div className="grid md:grid-cols-3 gap-8">
            <FeatureCard icon={<ClipboardList className="text-white"/>} title="Game Rules">A classic game of Truth or Dare. Complete tasks to earn points, change tasks for a small penalty, or skip turns and lose points!</FeatureCard>
            <FeatureCard icon={<Trophy className="text-white"/>} title="Scoring System">Earn +5 for completing a task, -2 for changing, and a harsh -6 for skipping. Compete for the top spot on the leaderboard!</FeatureCard>
            <FeatureCard icon={<UserCog className="text-white"/>} title="Admin Controls">Group admins have full control. They start and stop games, and are the only ones who can verify task completion to keep the game fair.</FeatureCard>
        </div>
    </div>
);

const LearnMorePage = () => (
    <div className="max-w-3xl mx-auto">
        <h1 className="text-4xl font-bold text-center mb-12 bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent">Bot Information & Guide</h1>
        
        <div className="space-y-12 text-gray-300">
            <section>
                <h2 className="text-2xl font-semibold mb-3 text-white border-b border-gray-700 pb-2">About the Game</h2>
                <p>Truth or Dare is a classic party game where players take turns choosing between answering a question truthfully or performing a dare. It&apos;s a fun way to get to know your friends better, share some laughs, and create memorable moments.</p>
            </section>

            <section>
                <h2 className="text-2xl font-semibold mb-3 text-white border-b border-gray-700 pb-2">How Our Bot Works</h2>
                <p className="mb-4">This bot automates the entire game process within your Telegram group. It manages player turns, provides random truth questions and dare tasks, keeps score, and saves the history of every game you play for you to view right here on this website.</p>
                <ul className="list-disc list-inside space-y-2 bg-gray-800/50 p-4 rounded-lg">
                    <li><span className="font-semibold">Fair Turn System:</span> The bot uses a queue to ensure every player gets a turn before anyone gets a second one.</li>
                    <li><span className="font-semibold">Vast Question Pool:</span> Hundreds of unique and interesting truth questions and dares are built-in to keep the game fresh.</li>
                    <li><span className="font-semibold">Admin Moderation:</span> Group admins are in charge. Only they can confirm if a task was completed, preventing cheating and keeping the game orderly.</li>
                </ul>
            </section>

            <section>
                <h2 className="text-2xl font-semibold mb-4 text-white border-b border-gray-700 pb-2">How to Play: Step-by-Step</h2>
                <div className="space-y-6 bg-gray-800/50 p-6 sm:p-8 rounded-2xl border border-white/10">
                    <div className="flex items-start space-x-4"><div className="flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-full bg-indigo-500 text-white font-bold text-lg">1</div><div><h3 className="text-xl font-semibold text-white mb-1">Add & Promote the Bot</h3><p>Add the <a href={`https://t.me/${BOT_USERNAME}?startgroup=true`} target="_blank" rel="noopener noreferrer" className="text-indigo-400 hover:underline">Truth or Dare Bot</a> to your group. You must promote it to an **admin** with message permissions for it to work.</p></div></div>
                    <div className="flex items-start space-x-4"><div className="flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-full bg-indigo-500 text-white font-bold text-lg">2</div><div><h3 className="text-xl font-semibold text-white mb-1">Start a New Game</h3><p>A group admin types <code className="bg-gray-700 px-2 py-1 rounded-md text-sm">/newgame</code> in the chat.</p></div></div>
                    <div className="flex items-start space-x-4"><div className="flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-full bg-indigo-500 text-white font-bold text-lg">3</div><div><h3 className="text-xl font-semibold text-white mb-1">Join the Lobby</h3><p>The bot will post a message with a &quot;Join Game&quot; button for players to click.</p></div></div>
                    <div className="flex items-start space-x-4"><div className="flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-full bg-indigo-500 text-white font-bold text-lg">4</div><div><h3 className="text-xl font-semibold text-white mb-1">Begin the Game</h3><p>An admin types <code className="bg-gray-700 px-2 py-1 rounded-md text-sm">/startgame</code>. The bot will randomly select the first player.</p></div></div>
                    <div className="flex items-start space-x-4"><div className="flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-full bg-indigo-500 text-white font-bold text-lg">5</div><div><h3 className="text-xl font-semibold text-white mb-1">Stop the Game</h3><p>An admin can end the session by typing <code className="bg-gray-700 px-2 py-1 rounded-md text-sm">/stop</code>.</p></div></div>
                    <div className="flex items-start space-x-4"><div className="flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-full bg-indigo-500 text-white font-bold text-lg">6</div><div><h3 className="text-xl font-semibold text-white mb-1">The Loop Continues!</h3><p>The bot automatically selects the next player after each turn until an admin stops the game.</p></div></div>
                </div>
            </section>
        </div>
        <p className="text-center text-xl text-cyan-400 mt-12 italic">
            We dare you to use this bot at least once! 😉
        </p>
    </div>
);

// --- Stats Dashboard Component ---
const StatsDashboard = () => {
  const [activeTab, setActiveTab] = useState<'group' | 'player'>('group');
  const [inputId, setInputId] = useState<string>('');
  const [groupStats, setGroupStats] = useState<GroupStats | null>(null);
  const [userStats, setUserStats] = useState<UserStatsData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  const clearState = () => { setInputId(''); setGroupStats(null); setUserStats(null); setError(''); };
  const handleTabChange = (tab: 'group' | 'player') => { setActiveTab(tab); clearState(); };

  const handleFetchStats = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!inputId) { setError(`Please enter a ${activeTab === 'group' ? 'Group' : 'Player'} ID.`); return; }
    setError(''); setIsLoading(true); setGroupStats(null); setUserStats(null);
    const endpoint = activeTab === 'group' ? 'stats' : 'user';
    try {
      const apiUrl = `http://localhost:8000/api/${endpoint}/${inputId}`;
      const response = await fetch(apiUrl);
      if (!response.ok) throw new Error(`${activeTab === 'group' ? 'Group' : 'Player'} ID not found.`);
      const data = await response.json();
      if (activeTab === 'group') setGroupStats(data);
      else setUserStats(data);
    } catch (err: unknown) {
        if (err instanceof Error) {
            setError(err.message);
        } else {
            setError('An unexpected error occurred.');
        }
    } finally { setIsLoading(false); }
  };

  return (
    <div>
        <div className="flex justify-center mb-4 border-b border-gray-700">
            <button onClick={() => handleTabChange('group')} className={`px-6 py-2 text-sm font-medium ${activeTab === 'group' ? 'border-b-2 border-indigo-400 text-white' : 'text-gray-400'}`}>Group Stats</button>
            <button onClick={() => handleTabChange('player')} className={`px-6 py-2 text-sm font-medium ${activeTab === 'player' ? 'border-b-2 border-indigo-400 text-white' : 'text-gray-400'}`}>Player Stats</button>
        </div>
        <form onSubmit={handleFetchStats} className="mb-12">
          <div className="relative max-w-lg mx-auto">
            <input type="text" value={inputId} onChange={(e) => setInputId(e.target.value)} placeholder={activeTab === 'group' ? 'Enter Group ID (e.g., -4615907473)' : 'Enter Player ID (e.g., 1756804399)'} className="w-full pl-12 pr-44 py-3 bg-gray-800 border border-gray-700 rounded-full focus:ring-2 focus:ring-indigo-500 focus:outline-none transition-all" />
            <div className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500">{activeTab === 'group' ? <Hash/> : <User/>}</div>
            <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center space-x-2">
              {(groupStats || userStats) && !isLoading && (<button type="button" onClick={clearState} className="p-2 bg-gray-700/50 text-gray-400 rounded-full hover:bg-red-500/50 hover:text-red-300 transition-colors" title="Clear Results"><X className="w-4 h-4"/></button>)}
              <button type="submit" disabled={isLoading} className="px-6 py-2 bg-indigo-600 rounded-full text-sm font-semibold hover:bg-indigo-500 transition-colors disabled:bg-gray-600 disabled:cursor-not-allowed">{isLoading ? 'Loading...' : 'Fetch'}</button>
            </div>
          </div>
          {error && <p className="text-center text-red-400 mt-3 text-sm">{error}</p>}
        </form>
        {groupStats && <div className="animate-fade-in"><h2 className="text-2xl font-bold mb-6 text-center text-gray-300">Displaying Stats for: <span className="text-indigo-400">{groupStats.groupName}</span></h2><div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12"><StatCard icon={<Gamepad2 size={24}/>} label="Total Games Played" value={groupStats.totalGames} color="bg-indigo-500/80" /><StatCard icon={<Crown size={24}/>} label="Highest Score Ever" value={groupStats.highestScore} color="bg-yellow-500/80" /><StatCard icon={<Users size={24}/>} label="Unique Players" value={groupStats.uniquePlayers} color="bg-cyan-500/80" /></div><div className="grid grid-cols-1 lg:grid-cols-3 gap-8"><div className="lg:col-span-2"><h3 className="text-xl font-semibold mb-4 flex items-center"><BarChart className="mr-2"/> Leaderboard</h3><div className="space-y-2">{groupStats.topPlayers.map((player, index) => (<PlayerRow key={index} rank={index + 1} {...player} />))}</div></div><div><h3 className="text-xl font-semibold mb-4 flex items-center"><History className="mr-2"/> Recent Games</h3><div className="space-y-4">{groupStats.gameHistory.slice().reverse().map((game, index) => (<GameHistoryCard key={index} {...game} />))}</div></div></div></div>}
        {userStats && <UserStatsDisplay data={userStats} />}
    </div>
  );
}


// --- Main Page Component ---
export default function HomePage() {
  const [currentPage, setCurrentPage] = useState<Page>('home');

  return (
    <main className="bg-gray-900 min-h-screen text-white font-sans">
      <div className="max-w-5xl mx-auto p-4 sm:p-8">
        <nav className="flex justify-between items-center mb-12">
            <div className="flex items-center space-x-2">
                <Gamepad2 className="w-7 h-7 text-indigo-400" />
                <span className="font-bold text-xl">Truth or Dare Bot</span>
            </div>
            <div className="flex items-center space-x-4 sm:space-x-6 text-sm sm:text-base">
                <button onClick={() => setCurrentPage('home')} className={`hover:text-indigo-400 transition-colors p-2 ${currentPage === 'home' ? 'text-indigo-400 font-semibold' : 'text-gray-400'}`}>Home</button>
                <button onClick={() => setCurrentPage('stats')} className={`hover:text-indigo-400 transition-colors p-2 ${currentPage === 'stats' ? 'text-indigo-400 font-semibold' : 'text-gray-400'}`}>Stats</button>
                <button onClick={() => setCurrentPage('learn')} className={`hover:text-indigo-400 transition-colors p-2 ${currentPage === 'learn' ? 'text-indigo-400 font-semibold' : 'text-gray-400'}`}>Learn More</button>
            </div>
        </nav>

        {currentPage === 'home' && (
            <div className="animate-fade-in">
                <HeroSection onNavigate={setCurrentPage} />
                <FeaturesSection />
            </div>
        )}

        {currentPage === 'stats' && (
            <div className="animate-fade-in">
                <StatsDashboard />
            </div>
        )}
        
        {currentPage === 'learn' && (
            <div className="animate-fade-in">
                <LearnMorePage />
            </div>
        )}

       <footer className="text-center mt-16 py-4 text-gray-500 text-sm border-t border-gray-800">
            <p>Made With ❤️ by Shreyash</p>
        </footer>
      </div>
    </main>
  );
}
