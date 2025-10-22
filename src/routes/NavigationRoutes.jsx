import { lazy } from 'react';

// project-imports
import Loadable from 'components/Loadable';
import DashboardLayout from 'layout/Dashboard';

// render - dashboard pages
const DefaultPages = Loadable(lazy(() => import('views/navigation/dashboard/Default')));
const GeronimoMonitorPage = Loadable(lazy(() => import('views/monitor/GeronimoMonitorPage')));
const PersonPage = Loadable(lazy(() => import('views/person/PersonPage')));
const ScriptExecutorPage = Loadable(lazy(() => import('views/scripts/ScriptExecutorPage')));

// ==============================|| NAVIGATION ROUTING ||============================== //

const NavigationRoutes = {
  path: '/',
  children: [
    {
      path: '/',
      element: <DashboardLayout />,
      children: [
        {
          path: '/',
          element: <DefaultPages />
        },
        {
          path: '/persons',
          element: <PersonPage />
        },
        {
          path: '/monitor-geronimo',
          element: <GeronimoMonitorPage />
        },
        {
          path: '/script-executor',
          element: <ScriptExecutorPage />
        }
      ]
    }
  ]
};

export default NavigationRoutes;