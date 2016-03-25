from .error import PackageError

class Overlay(object):

	def __init__(self, overlay):
		if not isinstance(overlay, dict):
			raise PackageError("An overlay has to be a dictionary not {t}".format(t=overlay.__class__.__name__))
		for (key, value) in overlay.items():
			setattr(self, key.replace("-", "_"), value)