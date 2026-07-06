type LoadingScreenProps = {
  message?: string;
};

export function LoadingScreen({ message = "Loading…" }: LoadingScreenProps) {
  return (
    <div className="page-shell flex items-center justify-center">
      <p className="text-sm text-foreground-secondary">{message}</p>
    </div>
  );
}
