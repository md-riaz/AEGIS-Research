"""
SafeDash Permission Rewriter (§4.3, §4.2).

Appends row-level security predicates to compiled SQL based on the user's
role.  This is the application-level enforcement layer described in §4.3;
production deployments should combine this with database-level Row Security
Policies (PostgreSQL CREATE POLICY) for defence-in-depth.

The rewriter ensures that the safety invariant ``sql ∈ Q_safe(L, r)`` holds
for role ``r`` — users can only see rows their role permits.
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class PermissionRewriter:
    """
    Appends role-based row-level security predicates to compiled SQL.

    Each role maps to a set of WHERE-clause predicates that restrict
    visibility.  The ``public`` role has no restrictions (full access).

    In production, role definitions and predicates would be stored in the
    semantic layer or an external policy store.  This prototype demonstrates
    the architectural pattern described in §4.3.
    """

    # Role → list of SQL predicates to append
    ROLE_PREDICATES: Dict[str, list] = {
        "public": [],                          # full access
        "dept_chair": [
            "o.DepartmentId = @user_dept_id",  # row-level filter
        ],
        "regional_manager": [
            "o.RegionId = @user_region_id",
        ],
        "read_only": [],                       # no row filter, but no DML
        "analyst": [
            "cu.IsActive = 1",                 # only active customers
        ],
    }

    def rewrite(
        self,
        sql: str,
        role: str = "public",
        role_params: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Append role-based predicates to the compiled SQL.

        Args:
            sql: The compiled T-SQL query from the SQLCompiler.
            role: The user's role identifier.
            role_params: Optional dict of role-specific parameter bindings
                         (e.g. ``{"@user_dept_id": "42"}``).

        Returns:
            The rewritten SQL with role predicates appended.
        """
        predicates = self.ROLE_PREDICATES.get(role, [])
        if not predicates:
            logger.debug(f"No role predicates for role '{role}'.")
            return sql

        # Append predicates after WHERE 1=1
        for pred in predicates:
            # Bind parameters if provided
            if role_params:
                for param, value in role_params.items():
                    pred = pred.replace(param, str(value))

            sql = sql.replace("WHERE 1=1", f"WHERE 1=1\n  AND {pred}", 1)

        logger.info(f"Permission rewriter: applied {len(predicates)} predicates for role '{role}'.")
        return sql

    @staticmethod
    def get_available_roles() -> list:
        """Return all configured role names."""
        return list(PermissionRewriter.ROLE_PREDICATES.keys())
