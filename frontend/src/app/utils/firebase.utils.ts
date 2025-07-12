import { environment } from '../../environments/environment';

export function getCollectionName(base: string): string {
  return environment.production ? base : `staging_${base}`;
}
