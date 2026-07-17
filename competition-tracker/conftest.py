# Anchors pytest's rootdir here so project modules (normalize, aggregate,
# diff_existing, ...) import cleanly regardless of where pytest is invoked
# from - no need for a src/ layout or editable install at this scale.
