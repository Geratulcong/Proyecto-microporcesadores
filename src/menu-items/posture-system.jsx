// Menú para Sistema de Posturas - Arduino + Raspberry Pi
const icons = { 
  person: <i className="ph ph-user" />,
  monitor: <i className="ph ph-activity" />,
  sensors: <i className="ph ph-pulse" />
};

const postureSystem = {
  id: 'group-posture-system',
  title: 'Sistema de Posturas',
  type: 'group',
  icon: icons.sensors,
  children: [
    {
      id: 'persons',
      title: 'Registrar Persona',
      type: 'item',
      icon: icons.person,
      url: '/persons'
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

export default postureSystem;