export function getOwnerToken(): string {
  let t = localStorage.getItem("cloudshare_owner");
  if (!t) {
    t = crypto.randomUUID();
    localStorage.setItem("cloudshare_owner", t);
  }
  return t;
}