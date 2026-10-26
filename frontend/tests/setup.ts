import '@testing-library/jest-dom/vitest';
import { beforeEach } from 'vitest';

beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
  // Existing component/journey tests represent an exploration session.
  sessionStorage.setItem('eletroprojeto:experience:v1:local', 'explore');
});
