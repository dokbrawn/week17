import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  vus: __ENV.CONCURRENCY ? parseInt(__ENV.CONCURRENCY) : 10,
  duration: '15s',
};

export default function () {
  const res = http.get('http://localhost:8085/api/shipments');
  check(res, { 'status is 200': (r) => r.status === 200 });
  sleep(0.5);
}