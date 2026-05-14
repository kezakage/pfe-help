import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, Compass, Users, BookOpen, Sparkles, MapPin, Bot } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { resourceToCard } from '../../data/projects.js'
import { heritage } from '../../lib/api.js'
import ProjectCard from '../../components/ProjectCard.jsx'

export default function Home() {
  const { t } = useTranslation()
  const [featured, setFeatured] = useState([])
  const [heroCards, setHeroCards] = useState([])
  useEffect(() => {
    heritage.resources({ limit: 4 })
      .then((data) => {
        const list = Array.isArray(data) ? data : (data.results || [])
        const cards = list.map(resourceToCard)
        setHeroCards(cards.slice(0, 4))
        setFeatured(cards.slice(0, 3))
      })
      .catch(() => {})
  }, [])
  return (
    <div>
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 -z-10"
             style={{ background: 'linear-gradient(135deg,#3e2417 0%, #67241a 60%, #a56432 100%)' }}/>
        <div className="absolute inset-0 -z-10 opacity-15"
             style={{ backgroundImage: 'repeating-linear-gradient(45deg, rgba(255,255,255,.5) 0 1px, transparent 1px 18px)' }}/>
        <div className="max-w-7xl mx-auto px-4 py-20 md:py-28 grid md:grid-cols-2 gap-10 items-center">
          <div className="text-white">
            <span className="chip bg-white/15 text-sand-100 backdrop-blur">{t('home.collaborativeBadge')}</span>
            <h1 className="font-display text-4xl md:text-6xl font-bold mt-4 leading-[1.05]">
              {t('home.heroTitleA')} <span className="text-sand-200">{t('home.heroTitleB')}</span>{t('home.heroTitleC')}
            </h1>
            <p className="mt-5 text-sand-100 text-lg max-w-xl">
              {t('home.heroBody')}
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link to="/explorer" className="btn-primary bg-white !text-terracotta-700 hover:!bg-sand-100">
                <Compass size={18}/>{t('home.exploreCta')}
                <ArrowRight size={16}/>
              </Link>
              <Link to="/inscription" className="btn-secondary !bg-white/10 !text-white !border-white/20 hover:!bg-white/20">
                {t('home.joinCta')}
              </Link>
            </div>
          </div>

          <div className="relative">
            <div className="grid grid-cols-2 gap-3">
              {heroCards.map((it) => (
                <div key={it.id} className="rounded-xl overflow-hidden h-32 md:h-40 relative shadow-soft"
                     style={{ background: `linear-gradient(135deg, ${it.coverColor}, #3e2417)` }}>
                  <div className="absolute inset-0 opacity-25"
                       style={{ backgroundImage: 'repeating-linear-gradient(45deg, rgba(255,255,255,.5) 0 1px, transparent 1px 12px)' }}/>
                  <div className="absolute bottom-3 start-3 text-white">
                    <div className="font-display text-lg font-semibold">{it.name}</div>
                    <div className="text-xs text-sand-200">{it.period}{it.region ? ` · ${it.region}` : ''}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-7xl mx-auto px-4 py-16">
        <h2 className="section-title text-center">{t('home.featuresTitle')}</h2>
        <p className="section-subtitle text-center max-w-2xl mx-auto">{t('home.featuresSubtitle')}</p>
        <div className="grid md:grid-cols-4 gap-5 mt-10">
          {[
            { icon: BookOpen, t: t('home.featPublicTitle'), d: t('home.featPublicBody') },
            { icon: Users, t: t('home.featCollabTitle'), d: t('home.featCollabBody') },
            { icon: Sparkles, t: t('home.featContentTitle'), d: t('home.featContentBody') },
            { icon: Bot, t: t('home.featToolsTitle'), d: t('home.featToolsBody') },
          ].map((f,i) => (
            <div key={i} className="card p-5">
              <div className="w-10 h-10 rounded-lg bg-terracotta-100 text-terracotta-700 grid place-items-center mb-3">
                <f.icon size={20}/>
              </div>
              <div className="font-semibold text-sand-900">{f.t}</div>
              <p className="text-sm text-sand-600 mt-1">{f.d}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Featured projects */}
      <section className="max-w-7xl mx-auto px-4 py-12">
        <div className="flex items-end justify-between mb-6">
          <div>
            <h2 className="section-title">{t('home.featuredTitle')}</h2>
            <p className="section-subtitle">{t('home.featuredSubtitle')}</p>
          </div>
          <Link to="/explorer" className="btn-secondary">{t('home.viewAll')} <ArrowRight size={16}/></Link>
        </div>
        <div className="grid md:grid-cols-3 gap-5">
          {featured.map(p => <ProjectCard key={p.id} project={p} to={`/explorer/${p.id}`}/>)}
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-7xl mx-auto px-4 my-16">
        <div className="card p-8 md:p-12 text-center bg-gradient-to-br from-sand-100 to-sand-50">
          <MapPin className="mx-auto text-terracotta-600" size={32}/>
          <h2 className="section-title mt-3">{t('home.ctaTitle')}</h2>
          <p className="section-subtitle max-w-2xl mx-auto">
            {t('home.ctaBody')}
          </p>
          <div className="mt-6 flex justify-center gap-3">
            <Link to="/inscription" className="btn-primary">{t('home.ctaCreateAccount')}</Link>
            <Link to="/connexion" className="btn-secondary">{t('home.ctaLogin')}</Link>
          </div>
        </div>
      </section>
    </div>
  )
}
