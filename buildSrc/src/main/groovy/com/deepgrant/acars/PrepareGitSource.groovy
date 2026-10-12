package com.deepgrant.acars

import javax.inject.Inject
import org.gradle.api.DefaultTask
import org.gradle.api.GradleException
import org.gradle.api.file.DirectoryProperty
import org.gradle.api.file.RegularFileProperty
import org.gradle.api.provider.MapProperty
import org.gradle.api.provider.Property
import org.gradle.api.tasks.*
import org.gradle.process.ExecOperations
import org.gradle.work.DisableCachingByDefault

@DisableCachingByDefault(because = 'Git checkouts contain machine-specific metadata.')
abstract class PrepareGitSource extends DefaultTask {
  @Input abstract Property<String> getRepositoryUrl()
  @Input abstract Property<String> getRevision()
  @Input abstract Property<Boolean> getOffline()
  @Input abstract MapProperty<String, String> getCommandEnvironment()
  @Optional @InputFile @PathSensitive(PathSensitivity.RELATIVE)
  abstract RegularFileProperty getPatchFile()
  @OutputDirectory abstract DirectoryProperty getSourceDirectory()
  @Inject abstract ExecOperations getExecOperations()

  private Map git(File directory, List<String> arguments, boolean allowFailure = false) {
    def output = new ByteArrayOutputStream()
    def error = new ByteArrayOutputStream()
    def result = execOperations.exec {
      workingDir directory
      commandLine(['git'] + arguments)
      environment commandEnvironment.get()
      standardOutput = output
      errorOutput = error
      ignoreExitValue = true
    }
    if (result.exitValue != 0 && !allowFailure) {
      throw new GradleException("git ${arguments[0]} failed: ${error.toString('UTF-8').trim()}")
    }
    [exit: result.exitValue, text: output.toString('UTF-8').trim()]
  }

  @TaskAction
  void prepare() {
    File source = sourceDirectory.get().asFile
    if (!source.exists() || source.list().length == 0) {
      if (offline.get()) {
        throw new GradleException('Pinned sources are missing. Run fetchSources without --offline first.')
      }
      source.parentFile.mkdirs()
      logger.lifecycle("Fetching ${repositoryUrl.get()} at ${revision.get()}")
      git(source.parentFile, ['clone', '--no-checkout', repositoryUrl.get(), source.absolutePath])
      git(source, ['checkout', '--detach', revision.get()])
    }
    if (!new File(source, '.git').isDirectory()) {
      throw new GradleException("Expected a Git checkout at ${source}; existing files were preserved.")
    }
    if (git(source, ['rev-parse', 'HEAD']).text != revision.get()) {
      throw new GradleException("Unexpected source revision at ${source}; existing edits were preserved.")
    }
    if (patchFile.isPresent()) {
      def patch = patchFile.get().asFile.absolutePath
      if (git(source, ['apply', '--reverse', '--check', patch], true).exit != 0) {
        git(source, ['apply', '--check', patch])
        git(source, ['apply', patch])
      }
    }
  }
}
