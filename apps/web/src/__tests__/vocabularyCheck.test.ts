import { describe, it, expect } from 'vitest';
import fs from 'fs';
import path from 'path';

// CA-45 / UI-32: Proibição terminante de termos eleitorais no frontend
const FORBIDDEN_ELECTORAL_TERMS = [
  'voto',
  'votação',
  'votacao',
  'eleição',
  'eleicao',
  'quórum de aprovação',
  'quorum de aprovacao',
  'candidato',
  'urna',
  'chapa',
];

function getAllSourceFiles(dir: string): string[] {
  let results: string[] = [];
  const list = fs.readdirSync(dir);
  for (const file of list) {
    const fullPath = path.join(dir, file);
    const stat = fs.statSync(fullPath);
    if (stat && stat.isDirectory()) {
      if (file !== '__tests__' && file !== 'node_modules') {
        results = results.concat(getAllSourceFiles(fullPath));
      }
    } else if (file.endsWith('.ts') || file.endsWith('.tsx')) {
      results.push(fullPath);
    }
  }
  return results;
}

describe('Conformidade de Vocabulário Não Eleitoral (CA-45, UI-32)', () => {
  it('não deve conter termos eleitorais proibidos no código fonte do frontend', () => {
    const srcDir = path.resolve(__dirname, '..');
    const files = getAllSourceFiles(srcDir);

    expect(files.length).toBeGreaterThan(10);

    const violations: { file: string; term: string; line: string }[] = [];

    for (const filePath of files) {
      const content = fs.readFileSync(filePath, 'utf-8');
      const lines = content.split('\n');

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const lower = line.toLowerCase();

        // Ignora comentários ou disclaimers que explicitamente negam os termos ("Não constitui voto...", "NÃO realiza votação...")
        if (
          lower.includes('não constitui voto') ||
          lower.includes('não realiza votação') ||
          lower.includes('veda terminantemente votações') ||
          lower.includes('sem voto')
        ) {
          continue;
        }

        for (const term of FORBIDDEN_ELECTORAL_TERMS) {
          // Busca palavra isolada
          const regex = new RegExp(`\\b${term}\\b`, 'i');
          if (regex.test(line)) {
            violations.push({
              file: path.relative(srcDir, filePath),
              term,
              line: line.trim(),
            });
          }
        }
      }
    }

    expect(violations).toEqual([]);
  });
});
