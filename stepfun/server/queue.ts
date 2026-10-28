let tail: Promise<void> = Promise.resolve();

/** Embedded seekdb is one native connection. Keep API calls off it one at a time. */
export function enqueue<T>(task: () => Promise<T>): Promise<T> {
  const run = tail.then(task, task);
  tail = run.then(
    () => undefined,
    () => undefined
  );
  return run;
}
