import { errorMessage } from './index';
import ptBR from './pt-BR.json';

function leaves(value: unknown, prefix = ''): [string, unknown][] {
  if (Array.isArray(value)) return [[prefix, value]];
  if (value && typeof value === 'object') {
    return Object.entries(value).flatMap(([key, child]) => leaves(child, prefix ? `${prefix}.${key}` : key));
  }
  return [[prefix, value]];
}

describe('pt-BR strings', () => {
  const all = leaves(ptBR);

  it('has no empty strings', () => {
    for (const [key, value] of all) {
      expect([key, typeof value === 'string' ? value.trim().length > 0 : true]).toEqual([key, true]);
    }
  });

  it('never mentions calories, weight or eating verbs (product rules)', () => {
    const forbidden = /calori|kcal|macro|peso|imc|saudável|comer|alimentar/i;
    for (const [key, value] of all) {
      expect([key, forbidden.test(JSON.stringify(value))]).toEqual([key, false]);
    }
  });

  it('translates every API error code used by the app', () => {
    expect(errorMessage('DAILY_LIMIT_REACHED')).toBe('Você usou as 2 fotos de hoje.');
    expect(errorMessage('SOMETHING_NEW')).toBe('Algo deu errado do nosso lado.');
  });
});
