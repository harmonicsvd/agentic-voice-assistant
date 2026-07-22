interface BrandBarProps {
  userSub: string;
}

export const BrandBar = ({ userSub }: BrandBarProps) => {
  const handleLogout = async () => {
    try {
      await fetch('/auth/logout', {
        method: 'POST',
        credentials: 'include'
      });
    } finally {
      window.location.href = '/login';
    }
  };

  return (
    <div className="brandbar">
      <div className="brand-copy">
        <div className="brand-name">Ram - Sham</div>
        <div className="brand-tag">Personal Work Assistant</div>
      </div>
      <button id="logoutBtn" className="logout-btn" type="button" onClick={handleLogout}>
        Log out
      </button>
    </div>
  );
};
