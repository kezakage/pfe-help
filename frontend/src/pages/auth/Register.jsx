import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../../context/AuthContext.jsx'

const DISCIPLINES = ['Architecture', 'Histoire', 'Archéologie', 'Sociologie', 'Urbanisme', 'Conservation', 'Autre']

export default function Register() {
  const { register } = useAuth()
  const { t } = useTranslation()
  const nav = useNavigate()
  const [data, setData] = useState({
    name: '', email: '', password: '', discipline: 'Architecture', institution: '', role: 'chercheur',
  })
  const set = (k) => (e) => setData({ ...data, [k]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    await register(data)
    nav('/verification-email')
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold">{t('auth.registerTitle')}</h1>
      <p className="text-sand-600 text-sm mt-1">{t('auth.registerSubtitle')}</p>

      <form onSubmit={submit} className="mt-6 space-y-3">
        <div>
          <label className="label">{t('auth.fullName')}</label>
          <input className="input" required value={data.name} onChange={set('name')} placeholder={t('auth.fullNamePlaceholder')}/>
        </div>
        <div>
          <label className="label">{t('auth.professionalEmail')}</label>
          <input type="email" className="input" required value={data.email} onChange={set('email')} placeholder={t('auth.emailPlaceholder')}/>
        </div>
        <div>
          <label className="label">{t('auth.password')}</label>
          <input type="password" className="input" required value={data.password} onChange={set('password')}/>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">{t('auth.discipline')}</label>
            <select className="input" value={data.discipline} onChange={set('discipline')}>
              {DISCIPLINES.map(d => <option key={d}>{d}</option>)}
            </select>
          </div>
          <div>
            <label className="label">{t('auth.requestedRole')}</label>
            <select className="input" value={data.role} onChange={set('role')}>
              <option value="chercheur">{t('auth.roleResearcher')}</option>
              <option value="expert">{t('auth.roleExpertPending')}</option>
            </select>
          </div>
        </div>
        <div>
          <label className="label">{t('auth.institution')}</label>
          <input className="input" value={data.institution} onChange={set('institution')} placeholder={t('auth.institutionPlaceholder')}/>
        </div>
        <label className="flex items-start gap-2 text-sm text-sand-700">
          <input type="checkbox" required className="mt-1"/>
          {t('auth.termsAccept')}
        </label>
        <button className="btn-primary w-full">{t('auth.submitRegister')}</button>
      </form>

      <div className="mt-6 text-center text-sm text-sand-600">
        {t('auth.hasAccount')} <Link to="/connexion" className="text-terracotta-700 font-medium">{t('auth.submit')}</Link>
      </div>
    </div>
  )
}
