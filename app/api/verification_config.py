from ..core.db_class.config import THEME_CHOICES, NAV_POSITION_CHOICES


class VerifConfig:

    @staticmethod
    def verif_update(data: dict) -> dict:
        result = {}

        if 'theme' in data:
            if data['theme'] not in THEME_CHOICES:
                return {'message': f"Invalid theme. Valid: {THEME_CHOICES}"}
            result['theme'] = data['theme']

        if 'nav_position' in data:
            if data['nav_position'] not in NAV_POSITION_CHOICES:
                return {'message': f"Invalid nav_position. Valid: {NAV_POSITION_CHOICES}"}
            result['nav_position'] = data['nav_position']

        if 'sidebar_collapsed' in data:
            if not isinstance(data['sidebar_collapsed'], bool):
                return {'message': 'sidebar_collapsed must be a boolean'}
            result['sidebar_collapsed'] = data['sidebar_collapsed']

        if not result:
            return {'message': 'No valid field provided'}

        return result
