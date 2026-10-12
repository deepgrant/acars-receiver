package com.deepgrant.acars

import java.nio.file.Files
import java.nio.file.StandardCopyOption
import org.gradle.api.DefaultTask
import org.gradle.api.file.ConfigurableFileCollection
import org.gradle.api.file.DirectoryProperty
import org.gradle.api.tasks.*
import org.gradle.work.DisableCachingByDefault

@DisableCachingByDefault(because = 'The destination also holds locally received data.')
abstract class InstallReceiver extends DefaultTask {
  @InputDirectory @PathSensitive(PathSensitivity.RELATIVE)
  abstract DirectoryProperty getSourceDirectory()
  @Internal abstract DirectoryProperty getDestinationDirectory()
  @OutputFiles abstract ConfigurableFileCollection getInstalledFiles()

  @TaskAction
  void install() {
    File source = sourceDirectory.get().asFile
    File destination = destinationDirectory.get().asFile
    // Replace each owned program file by rename. Existing open executable/library
    // handles keep their original inode; data/ is neither copied nor deleted.
    def targets = installedFiles.files.toList().sort { file -> file.name == 'acarsdec' ? 1 : 0 }
    targets.each { target ->
      def relative = destination.toPath().relativize(target.toPath())
      def input = source.toPath().resolve(relative)
      target.parentFile.mkdirs()
      def temporary = Files.createTempFile(target.parentFile.toPath(), '.receiver-install-', '.tmp')
      try {
        Files.copy(input, temporary, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.COPY_ATTRIBUTES)
        if (relative.toString().startsWith('bin/') || target.name.endsWith('.command')) {
          temporary.toFile().setExecutable(true, false)
        }
        Files.move(temporary, target.toPath(), StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE)
      } finally {
        Files.deleteIfExists(temporary)
      }
    }
    logger.lifecycle("Installed receiver at ${destination}; reception logs were preserved.")
  }
}
