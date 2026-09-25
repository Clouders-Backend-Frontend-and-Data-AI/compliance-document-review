// Turns an axios error into a message that actually says what went wrong,
// instead of every failure mode looking identical to the user.
export function getErrorMessage(err, fallback = "Something went wrong. Please try again.") {
  if (!err) return fallback;

  // The server responded, but with an error status (4xx/5xx).
  if (err.response) {
    const detail = err.response.data?.detail;
    if (typeof detail === "string") return detail;
    // FastAPI validation errors come back as a list of {msg, loc} objects.
    if (Array.isArray(detail) && detail.length > 0) {
      return detail.map((d) => d.msg || JSON.stringify(d)).join("; ");
    }
    if (err.response.status === 401) return "Incorrect email or password.";
    if (err.response.status === 403) return "You don't have permission to do that.";
    if (err.response.status === 404) return "That wasn't found — it may have been removed.";
    if (err.response.status >= 500) {
      return "The server hit an error processing that request. Try again shortly.";
    }
    return `Request failed (status ${err.response.status}).`;
  }

  // The request went out but never got a response — network issue, CORS
  // block, timeout, or the server is simply down/asleep.
  if (err.request) {
    return "Couldn't reach the server. It may be offline, waking up from sleep, or blocked by a network/CORS issue — check that the backend is running and reachable.";
  }

  // Something failed before the request was even sent.
  return err.message || fallback;
}
