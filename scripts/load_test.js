import http from "k6/http";
import { check } from "k6";

export const options = {
  stages: [
    { duration: "10s", target: 50 },
    { duration: "30s", target: 50 },
  ],
};

const BASE = __ENV.TARGET;

export default function () {
  const res = http.batch([
    ["GET", `${BASE}/`],
    ["GET", `${BASE}/assets/index-CDVaWVA4.css`],
    ["GET", `${BASE}/assets/index-DvZZPmyC.js`],
  ]);
  check(res[0], { "status 200": (r) => r.status === 200 });
}
