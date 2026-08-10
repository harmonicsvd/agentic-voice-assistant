import { useNavigate } from 'react-router-dom';

interface BrandBarProps {
  userSub: string;
}

export const BrandBar = ({ userSub }: BrandBarProps) => {
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await fetch('/auth/logout', {
        method: 'POST',
        credentials: 'include'
      });
    } finally {
      window.location.href = '/login'; // Redirect to login page
    }
  };

  return (
    <div className="brandbar">
      <div className="brand-copy">
        <div className="brand-name">Ram - Sham</div>
        <div className="brand-tag">Personal Work Assistant</div>
      </div>
      <div className="brand-actions">
        <button className="nav-btn" type="button" onClick={() => navigate('/assistant')}>
          Assistant
        </button>
        <button className="nav-btn" type="button" onClick={() => navigate('/profile')}>
          Profile
        </button>
        <button className="nav-btn" type="button" onClick={() => navigate('/documents')}>
          Documents
        </button>
        <button className="logout-btn" type="button" onClick={handleLogout}>
          Logout
        </button>
      </div>
    </div>
  );
};
