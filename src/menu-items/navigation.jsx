const icons = { 
  dashboard: <i className="ph ph-house-line" />, 
  layouts: <i className="ph ph-house-line" />,
  monitor: <i className="ph ph-activity" />
};

const navigation = {
  id: 'group-dashboard-loading-unique',
  title: 'Navigation',
  type: 'group',
  icon: icons.dashboard,
  children: [
    {
      id: 'dashboard',
      title: 'Dashboard',
      type: 'item',
      icon: icons.dashboard,
      url: '/'
    },
    {
      id: 'monitor-geronimo',
      title: 'Monitor Geronimo',
      type: 'item',
      icon: icons.monitor,
      url: '/monitor-geronimo'
    }
  ]
};

export default navigation;
