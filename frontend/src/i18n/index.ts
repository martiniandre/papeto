import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import ptBR from './pt-BR.json';

export const defaultNS = 'translation';
export const resources = { 'pt-BR': { translation: ptBR } } as const;

if (!i18n.isInitialized) {
  void i18n.use(initReactI18next).init({
    resources,
    lng: 'pt-BR',
    fallbackLng: 'pt-BR',
    defaultNS,
    interpolation: { escapeValue: false },
    returnNull: false,
    initAsync: false,
  });
}

/** Translates a backend error code (docs/api.md: "the app translates code"). */
export function errorMessage(code: string): string {
  const key = `errors.${code}`;
  const translate = i18n.t.bind(i18n) as (k: string) => string;
  return translate(i18n.exists(key) ? key : 'errors.UNKNOWN_ERROR');
}

export default i18n;
