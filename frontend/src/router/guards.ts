import type { Role } from "../types/api";
import { restoreSession, session } from "../stores/session";
import { router } from "./index";

router.beforeEach(async (to) => {
  if (to.path === "/login") {
    if (!session.user && session.token) await restoreSession();
    return session.user ? "/activities" : true;
  }

  if (!session.user) await restoreSession();
  if (!session.user) return "/login";

  const roles = to.meta.roles as Role[] | undefined;
  if (roles && !roles.includes(session.user.role)) return "/activities";
  return true;
});
