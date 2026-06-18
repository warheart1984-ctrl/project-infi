export async function captureBrowserSnapshot(path = window.location.pathname) {
  return {
    path,
    title: document.title,
    url: window.location.href,
    text: document.body?.innerText?.slice(0, 4000) || '',
    capturedAt: new Date().toISOString(),
  };
}
