""" Application-wide constants """

kMaximumWorkerThreads = 8 # Number of images to process in parallel
kMinimumDatabaseConnections = 0 # Minimum number of connections to database
kMaximumDatabaseConnections = kMaximumWorkerThreads + 2 # Maximum number of connections to database
kMetadataFile = 'metadata.json' # Filename containing global metadata for a directory
kTimestampFormat = '%Y-%m-%dT%H:%M:%SZ' # ISO-8601 date format, UTC required
kImageDirectory = '/data/vision/images' # Directory for image storage
