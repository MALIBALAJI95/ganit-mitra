plugins {
    kotlin("jvm")
}

dependencies {
    implementation(project(":math"))
    testImplementation(kotlin("test"))
    testImplementation("org.junit.jupiter:junit-jupiter:5.10.2")
}

tasks.test {
    useJUnitPlatform()
    maxHeapSize = "1024m"
}

kotlin {
    jvmToolchain(17)
}
