import React, { useCallback, useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './styles.css'

const mock = {
  user: 'Maya', zodiac: 'Scorpio', persona: 'Moon Reader', mood: 'Curious',
  diamonds: 240, streak: 7,
}

const tarotDeck = [
  { number: 'XVII', name: 'The Star', symbol: '✦', message: 'Hope returns when you make room for a softer kind of certainty.' },
  { number: 'II', name: 'The High Priestess', symbol: '☾', message: 'The answer is already speaking; listen before you reach for proof.' },
  { number: 'XIX', name: 'The Sun', symbol: '☼', message: 'Let the visible joy count. You do not need to earn every bright thing.' },
]
const horoscopeFocus = ['Today', 'Love', 'Work', 'Inner world']
const zodiacOptions = ['Scorpio', 'Aries', 'Leo', 'Pisces']

function Brand() {
  return <a className="brand" href="/"><span className="brand-star">✦</span><span>Fortunis8</span></a>
}

function PublicNav() {
  return <header className="public-nav"><Brand /><nav><a href="#ritual">The ritual</a><a href="#readings">Readings</a><a href="/login">Sign in</a><a className="nav-cta" href="/dashboard">Get Your Reading <span>↗</span></a></nav></header>
}

function TarotCard({ number, name, symbol, tone = '', onSelect, selected }) {
  return <button type="button" aria-label={`Reveal ${name}`} aria-pressed={selected} onClick={onSelect} className={`tarot-card ${tone} ${selected ? 'selected' : ''}`}><span className="tarot-number">{number}</span><div className="tarot-symbol">{symbol}</div><span className="tarot-name">{name}</span></button>
}

function Landing() {
  const [selectedTarot, setSelectedTarot] = useState('XVII')
  const selectedCard = tarotDeck.find((card) => card.number === selectedTarot)
  return <main className="site-page landing-page">
    <div className="ambient ambient-one" /><div className="ambient ambient-two" />
    <PublicNav />
    <section className="landing-hero">
      <div className="hero-copy">
        <p className="eyebrow">PERSONALIZED FORTUNE · EVERY DAY</p>
        <h1>Meet the version of you that is <em>waiting to be discovered.</em></h1>
        <p className="hero-lede">Fortunis8 turns your zodiac, mood, and inner compass into a daily ritual of insight — part reflection, part wonder, entirely yours.</p>
        <div className="hero-actions"><a className="primary-button" href="/dashboard">Get Your Reading <span>↗</span></a><a className="text-link" href="#ritual">Explore the ritual <span>↓</span></a></div>
        <p className="hero-note"><span className="note-dot" /> A few quiet minutes. A clearer point of view.</p>
      </div>
      <div className="hero-art" aria-label="Preview of a personalized tarot reading">
        <div className="orbit orbit-one" /><div className="orbit orbit-two" />
        <div className="hero-spark spark-a">✦</div><div className="hero-spark spark-b">·</div>
        <div className="tarot-fan"><TarotCard {...tarotDeck[1]} tone="behind" selected={selectedTarot === 'II'} onSelect={() => setSelectedTarot('II')} /><TarotCard {...tarotDeck[0]} tone="featured" selected={selectedTarot === 'XVII'} onSelect={() => setSelectedTarot('XVII')} /><TarotCard {...tarotDeck[2]} tone="behind sun" selected={selectedTarot === 'XIX'} onSelect={() => setSelectedTarot('XIX')} /></div>
        <div className="tarot-reveal"><span className="reveal-label">{selectedCard.name.toUpperCase()} · YOUR CARD</span><p>{selectedCard.message}</p><span className="tap-hint">Tap a card to reveal another perspective</span></div>
        <div className="art-caption"><span className="caption-line" /><span>CHOOSE A CARD TO BEGIN</span></div>
      </div>
    </section>

    <section className="trust-row"><span>Made for the questions you carry quietly</span><span className="trust-rule" /><span>Fortune · Tarot · Horoscope</span></section>

    <section className="experience-section" id="ritual">
      <div className="section-intro"><p className="eyebrow">A RITUAL, NOT A RUSH</p><h2>Look inward.<br /><em>Move forward.</em></h2><p>Every reading begins with where you are — your sky, your season, your mood — and leaves you with something to carry into the day.</p></div>
      <div className="preview-stack">
        <article className="insight-preview"><div className="preview-top"><span className="mini-icon">☼</span><span className="preview-type">DAILY FORTUNE</span><span className="preview-more">•••</span></div><h3>Today asks you to trust the quiet pull.</h3><p>Not every answer arrives with a flash. Give the small knowing in your chest enough room to become a direction.</p><div className="preview-footer"><span>For Maya · Scorpio</span><span className="gold-arrow">↗</span></div></article>
        <article className="identity-preview"><div className="identity-orbit"><span>♏</span></div><div><p className="preview-type">YOUR INNER COMPASS</p><h3>Moon Reader</h3><p>Intuitive · Observant · Deeply curious</p></div><span className="edit-mark">✎</span></article>
      </div>
    </section>

    <section className="reading-types" id="readings"><div className="types-heading"><p className="eyebrow">CHOOSE YOUR DOORWAY</p><h2>There is more than one way<br /><em>to find a little light.</em></h2></div><div className="type-grid"><a className="type-card fortune" href="/dashboard"><span className="type-symbol">☼</span><span className="type-index">01</span><h3>Daily fortune</h3><p>A grounded perspective for the day ahead.</p><span className="card-arrow">↗</span></a><a className="type-card tarot" href="/dashboard"><span className="type-symbol">✦</span><span className="type-index">02</span><h3>Tarot</h3><p>Ask a question. Draw a new way of seeing.</p><span className="card-arrow">↗</span></a><a className="type-card horoscope" href="/dashboard"><span className="type-symbol">☾</span><span className="type-index">03</span><h3>Horoscope</h3><p>Let the sky put today in perspective.</p><span className="card-arrow">↗</span></a></div></section>

    <section className="landing-bottom"><div><span className="brand-star">✦</span><h2>Your next chapter<br /><em>starts with a question.</em></h2></div><a className="primary-button" href="/dashboard">Get Your Reading <span>↗</span></a></section>
    <footer className="site-footer"><Brand /><span>Private by intention · Made for reflection</span><span>© Fortunis8</span></footer>
  </main>
}

function AppShell({ children, active = 'Today' }) {
  const links = [['Today', '/dashboard', '✦'], ['Readings', '/dashboard#readings', '◒'], ['Quests', '/dashboard#quests', '♢'], ['History', '/dashboard#history', '↺'], ['Profile', '/dashboard#profile', '♙']]
  return <main className="app-page"><header className="app-topbar"><Brand /><div className="preview-badge">PREVIEW · SAMPLE DATA</div><div className="app-user"><span className="avatar">M</span><span className="user-name">Maya</span><span>⌄</span></div></header><div className="app-layout"><aside className="app-sidebar"><p className="sidebar-label">YOUR RITUAL</p>{links.map(([label, href, icon]) => <a className={active === label ? 'active' : ''} href={href} key={label}><span>{icon}</span>{label}</a>)}<div className="sidebar-bottom"><div className="diamond-mini">◇ <strong>{mock.diamonds}</strong><span>diamonds</span></div><a href="/">↪ Leave preview</a></div></aside><section className="app-content">{children}</section></div><nav className="mobile-nav">{links.map(([label, href, icon]) => <a className={active === label ? 'active' : ''} href={href} key={label}><span>{icon}</span>{label}</a>)}</nav></main>
}

function Dashboard() {
  const [focus, setFocus] = useState('Today')
  const [sign, setSign] = useState(mock.zodiac)
  return <AppShell><div className="dashboard-head"><div><p className="eyebrow">TUESDAY · OCTOBER 24</p><h1>Good morning, <em>Maya.</em></h1><p>Here is what your inner compass is pointing toward today.</p></div><div className="dashboard-actions"><span className="dashboard-diamond">◇ <strong>{mock.diamonds}</strong></span><span className="streak-pill">✦ {mock.streak} day streak</span></div></div>
    <section className="identity-strip"><div className="zodiac-medallion">♏</div><div><p className="card-label">YOUR CELESTIAL PROFILE</p><h2>Scorpio <span>·</span> {mock.persona}</h2><p>Feeling <strong>{mock.mood.toLowerCase()}</strong> today</p></div><a href="#profile" className="small-action">Edit profile ↗</a></section>
    <section className="dashboard-grid"><article className="daily-card"><div className="card-top"><span className="eyebrow">YOUR DAILY INSIGHT</span><span className="insight-date">OCT 24</span></div><h2>Today asks you to trust the quiet pull.</h2><p>Not every answer arrives with a flash. Give the small knowing in your chest enough room to become a direction.</p><div className="daily-bottom"><span>Personalized for your Moon Reader energy</span><a href="#readings">Read in full ↗</a></div></article><aside className="streak-card"><div className="streak-orbit">✦</div><p className="card-label">CURRENT STREAK</p><div className="streak-number">{mock.streak}<span> days</span></div><p>Keep your ritual close. Your next milestone is in 3 days.</p><div className="streak-progress"><span style={{ width: '70%' }} /></div><span className="progress-caption">7 of 10 days</span></aside></section>
    <section className="dashboard-section" id="readings"><div className="section-title"><div><p className="eyebrow">MAKE A MOMENT OF IT</p><h2>What are you listening for?</h2></div><a href="#readings">View all ↗</a></div><div className="dashboard-reading-grid"><a href="#" className="reading-entry entry-fortune"><span className="entry-icon">☼</span><span className="entry-number">01</span><h3>Daily fortune</h3><p>A little clarity for the road ahead.</p><span className="entry-arrow">↗</span></a><a href="#" className="reading-entry entry-tarot"><span className="entry-icon">✦</span><span className="entry-number">02</span><h3>Tarot draw</h3><p>One question. Three possibilities.</p><span className="entry-arrow">↗</span></a><a href="#" className="reading-entry entry-horoscope"><span className="entry-icon">☾</span><span className="entry-number">03</span><h3>Horoscope</h3><p>Your sky, translated for today.</p><span className="entry-arrow">↗</span></a></div></section>
    <section className="horoscope-panel"><div className="horoscope-copy"><p className="eyebrow">PERSONALIZE YOUR HOROSCOPE</p><h2>Let the sky meet you <em>where you are.</em></h2><p>Choose a lens for your sample forecast. In the real product, this preference will shape your saved reading.</p></div><div className="horoscope-controls"><div><span className="control-label">YOUR SIGN</span><div className="option-row">{zodiacOptions.map((option) => <button type="button" className={`option-chip ${sign === option ? 'chosen' : ''}`} onClick={() => setSign(option)} key={option}>{option}</button>)}</div></div><div><span className="control-label">FOCUS FOR TODAY</span><div className="option-row">{horoscopeFocus.map((option) => <button type="button" className={`option-chip ${focus === option ? 'chosen' : ''}`} onClick={() => setFocus(option)} key={option}>{option}</button>)}</div></div><div className="horoscope-preview"><span>MOCK FORECAST · {sign.toUpperCase()} · {focus.toUpperCase()}</span><strong>Your attention is your most powerful constellation today.</strong></div></div></section>
    <section className="lower-dashboard"><article className="quest-panel" id="quests"><div className="section-title"><div><p className="eyebrow">A LITTLE MOMENTUM</p><h2>Today's quests</h2></div><a href="#quests">See all ↗</a></div><div className="quest-item"><span className="quest-icon">☼</span><div><h3>Meet the day</h3><p>Complete your daily reading</p><div className="quest-bar"><span style={{ width: '33%' }} /></div></div><strong>+10 ◇</strong></div><div className="quest-item"><span className="quest-icon">✦</span><div><h3>Look twice</h3><p>Explore a tarot draw</p><div className="quest-bar"><span style={{ width: '0%' }} /></div></div><strong>+20 ◇</strong></div></article><article className="history-panel" id="history"><div className="section-title"><div><p className="eyebrow">YOUR ARCHIVE</p><h2>Recent reflections</h2></div><a href="#history">History ↗</a></div><div className="history-item"><span className="history-icon">✦</span><div><h3>The Star</h3><p>Tarot · Yesterday</p></div><span>↗</span></div><div className="history-item"><span className="history-icon">☼</span><div><h3>A softer beginning</h3><p>Daily fortune · Oct 22</p></div><span>↗</span></div></article></section>
    <p className="mock-disclaimer">Preview only · The content above is illustrative sample data and is not connected to an account or live reading service.</p>
  </AppShell>
}

function TechnicalPoc() {
  const [status, setStatus] = useState({ state: 'checking', message: 'Checking the reading room…' })
  const simulateOffline = new URLSearchParams(window.location.search).get('simulate') === 'offline'
  const checkBackend = useCallback(async () => { setStatus({ state: 'checking', message: 'Checking the reading room…' }); try { if (simulateOffline) throw new Error('Simulated backend outage for POC validation.'); const response = await fetch('/health'); if (!response.ok) throw new Error(`Backend returned ${response.status}`); const data = await response.json(); setStatus({ state: 'online', message: data.message || 'Backend is online.' }) } catch (error) { setStatus({ state: 'offline', message: error.message || 'The backend could not be reached.' }) } }, [simulateOffline])
  useEffect(() => { checkBackend() }, [checkBackend])
  return <main className="technical-page"><a href="/" className="technical-back">← Back to Fortunis8</a><p className="eyebrow">INTERNAL TECHNICAL POC</p><h1>Hybrid connectivity test</h1><p className="technical-copy">This route is retained for infrastructure validation and is not the customer-facing product.</p><section className={`connection-card ${status.state}`}><div className="card-heading"><span className="status-dot" /><div><p className="card-label">BACKEND SIGNAL</p><h2>{status.state === 'online' ? 'The room is open.' : status.state === 'offline' ? 'The room is quiet.' : 'Listening for the signal…'}</h2></div></div><p className="status-copy">{status.message}</p>{status.state === 'online' && <p className="proof">✓ React → <code>/health</code> → FastAPI</p>}{status.state === 'offline' && <button type="button" onClick={checkBackend}>Try the connection again</button>}</section></main>
}

function App() {
  const path = window.location.pathname
  if (path === '/dashboard') return <Dashboard />
  if (path === '/technical-poc') return <TechnicalPoc />
  return <Landing />
}

createRoot(document.getElementById('root')).render(<App />)
